from rest_framework import viewsets, status, parsers, permissions
from .models import Document
from .serializers import DocumentSerializer, DocumentUploadSerializer
from .services import DocumentProcessingService

from core.utils import Response

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

    def list(self, request, *args, **kwargs):
        """List all documents for the current user's tenant"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            status=status.HTTP_200_OK,
            message="Documents retrieved successfully",
            data=serializer.data,
            additional_info={
                "total_count": queryset.count(),
                "tenant_id": (
                    str(request.user.tenant.id)
                    if hasattr(request.user, "tenant")
                    else None
                ),
            },
        )

    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific document"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(
            status=status.HTTP_200_OK,
            message=f"Document '{instance.original_filename}' retrieved successfully",
            data=serializer.data,
            additional_info={
                "processing_status": instance.status,
                "file_size_bytes": instance.file_size,
            },
        )

    def update(self, request, *args, **kwargs):
        """Update document metadata (limited fields)"""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        return Response(
            status=status.HTTP_200_OK,
            message=f"Document '{updated_instance.original_filename}' updated successfully",
            data=serializer.data,
            additional_info={
                "document_id": str(updated_instance.id),
                "update_type": "partial" if partial else "full",
            },
        )

    def destroy(self, request, *args, **kwargs):
        """Delete a document"""
        instance = self.get_object()
        filename = instance.original_filename
        document_id = str(instance.id)

        self.perform_destroy(instance)
        return Response(
            status=status.HTTP_204_NO_CONTENT,
            message=f"Document '{filename}' deleted successfully",
            additional_info={"deleted_document_id": document_id},
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
                    status=status.HTTP_400_BAD_REQUEST,
                    message="Tenant required for document upload",
                    error_details={
                        "tenant": [
                            "Superusers must specify a tenant when uploading documents"
                        ]
                    },
                )
            else:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    message="Tenant required for document upload",
                    error_details={
                        "tenant": ["User must belong to a tenant to upload documents"]
                    },
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
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Failed to process document",
                error_details={"processing": [str(e)]},
                additional_info={
                    "document_id": str(doc.id),
                    "filename": doc.original_filename,
                },
            )

        # Return the details of the processed document
        doc.refresh_from_db()
        response_serializer = self.get_serializer(doc)
        return Response(
            status=status.HTTP_201_CREATED,
            message=f"Document '{doc.original_filename}' uploaded and processed successfully",
            data=response_serializer.data,
            additional_info={
                "document_id": str(doc.id),
                "processing_status": doc.status,
                "file_size_bytes": doc.file_size,
                "page_count": doc.page_count,
            },
        )
