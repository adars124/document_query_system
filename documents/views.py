from rest_framework import viewsets, status, parsers, permissions
from rest_framework.response import Response
from .models import Document
from .serializers import DocumentSerializer, DocumentUploadSerializer
from .services import DocumentProcessingService

import pprint


class DocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for uploading, listing, and managing documents.
    """

    serializer_class = DocumentSerializer
    # Allow file uploads
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Ensure users can only access documents within their own tenant.
        if not hasattr(self.request.user, "tenant") or self.request.user.tenant is None:
            return Document.objects.none()
        return Document.objects.filter(tenant=self.request.user.tenant).order_by(
            "-uploaded_at"
        )

    def create(self, request, *args, **kwargs):
        """
        Handles the file upload.
        """
        document_processor = DocumentProcessingService(tenant_id=request.user.tenant.id)

        # Check if user has a tenant (superusers might not have one)
        if not hasattr(request.user, "tenant") or request.user.tenant is None:
            if request.user.is_superuser:
                return Response(
                    {
                        "error": "Superusers must specify a tenant when uploading documents"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response(
                    {"error": "User must belong to a tenant to upload documents"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        upload_serializer = DocumentUploadSerializer(data=request.data)
        upload_serializer.is_valid(raise_exception=True)

        file = upload_serializer.validated_data["file"]

        # Create the initial Document record
        doc = Document.objects.create(
            tenant=request.user.tenant,
            uploaded_by=request.user,
            original_file=file,
            original_filename=file.name,
            file_size=file.size,
        )

        try:
            # Trigger the processing pipeline (synchronous for now)
            document_processor.process_document(doc.id)
        except Exception as e:
            # The service already marked the doc as FAILED, but we return a server error
            return Response(
                {"error": "Failed to process document", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Return the details of the processed document
        doc.refresh_from_db()
        response_serializer = self.get_serializer(doc)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
