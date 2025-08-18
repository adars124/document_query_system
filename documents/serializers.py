from rest_framework import serializers
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "tenant",
            "original_filename",
            "file_size",
            "page_count",
            "status",
            "uploaded_at",
            "processed_at",
            "error_message",
        ]
        read_only_fields = fields  # All fields are read-only in this serializer


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField(help_text="The document file to be uploaded.")
