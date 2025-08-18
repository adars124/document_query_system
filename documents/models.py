import uuid
from enum import Enum
from pathlib import Path
from typing import Optional

from django.db import models
from django.conf import settings

from pydantic import BaseModel


class ChunkWithPage(BaseModel):
    """
    Represents a text chunk with page information from the chunking process.
    """

    text: str
    page_number: Optional[int] = None


class OcrEngine(Enum):
    RAPID_OCR = "rapidocr"
    TESSERACT_OCR = "tesseract"


class DeviceType(Enum):
    CPU = "cpu"
    CUDA = "cuda"


def get_upload_path(instance, filename):
    # Return relative path for Django FileField upload_to
    return f"{instance.tenant.id}/uploads/{filename}"


class Document(models.Model):
    class ProcessingStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "users.Tenant", on_delete=models.CASCADE, related_name="documents"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    original_file = models.FileField(upload_to=get_upload_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    page_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
    )
    metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.original_filename

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ["-uploaded_at"]  # Order documents by uploaded date (newest first)
        indexes = [
            models.Index(fields=["tenant", "status"]),  # Index for tenant and status
            models.Index(fields=["original_filename"]),  # Index for original_filename
        ]
