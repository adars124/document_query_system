import os
from pathlib import Path
from typing import List
from urllib.parse import urlparse
from dataclasses import dataclass

from django.conf import settings
from django.utils import timezone
from torch.cpu import is_available
from .models import Document

import torch
import weaviate
import weaviate.classes as wvc

from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.chunking import HybridChunker
from docling.datamodel.pipeline_options import (
    AcceleratorDevice,
    AcceleratorOptions,
    PdfPipelineOptions,
    OcrMacOptions,
    TesseractCliOcrOptions,
)
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
    WordFormatOption,
)
from docling_core.types.doc import ImageRefMode, DoclingDocument
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer

from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from transformers import AutoTokenizer

from .models import OcrEngine, DeviceType, ChunkWithPage


# Extraction using Docling
class ExtractionService:
    """
    Service to handle document content and image extraction using docling.
    """

    def __init__(self, ocr_engine: OcrEngine = OcrEngine.RAPID_OCR):
        """
        Initializes the document converter with specific options.
        Using CUDA if available, otherwise CPU.
        """
        accelerator_options = AcceleratorOptions(
            num_threads=8, device=AcceleratorDevice.AUTO
        )
        pipeline_options = PdfPipelineOptions(
            accelerator_options=accelerator_options,
            do_ocr=True,
            do_table_structure=True,
            generate_picture_images=True,
            images_scale=settings.IMAGE_SCALE,
        )
        pipeline_options.table_structure_options.do_cell_matching = True

        if ocr_engine == OcrEngine.TESSERACT_OCR:
            print("Using Tesseract OCR")
            pipeline_options.ocr_options = TesseractCliOcrOptions(
                lang=["auto"], force_full_page_ocr=True
            )

        self.converter = DocumentConverter(
            allowed_formats=settings.ALLOWED_FORMATS,
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options, backend=PyPdfiumDocumentBackend
                )
            },
        )

    def extract(self, file_path: Path, tenant_id: str):
        """
        Extracts markdown and images from a document.

        Args:
            file_path: The path to the document to process.
            tenant_id: The ID of the tenant.

        Returns:
            A tuple containing the path to the markdown file, the image directory, and the DoclingDocument object.
        """
        base_output_path = Path(settings.MEDIA_ROOT) / str(tenant_id)
        markdown_dir = base_output_path / "markdown"
        image_dir = base_output_path / "images"

        os.makedirs(markdown_dir, exist_ok=True)
        os.makedirs(image_dir, exist_ok=True)

        file_stem = file_path.stem
        markdown_output_path = markdown_dir / f"{file_stem}.md"

        try:
            # Perform the conversion
            conversion_result = self.converter.convert(str(file_path))
            doc = conversion_result.document

            # Save the markdown with referenced images
            # Use relative path to avoid creating nested tenant_id directories
            doc.save_as_markdown(
                filename=markdown_output_path,
                image_mode=ImageRefMode.REFERENCED,
                artifacts_dir=Path("../images"),
            )

            return markdown_output_path, image_dir, doc

        except Exception as e:
            # TODO: Add more robust error handling
            print(f"Error during document conversion: {e}")
            raise


# Embedding generation using sentence-transformers
class EmbeddingService:
    """
    Service for chunking text and generating embeddings using Docling's hybrid chunker.
    """

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        """
        Initializes the hybrid chunker and embedding model.
        """
        device = DeviceType.CPU

        # Use 'cuda' if GPU is available
        if torch.cuda.is_available():
            device = DeviceType.CUDA

        self.embedding_model = HuggingFaceEmbeddings(
            model_name=model_name, model_kwargs={"device": device.value}
        )

        # Initialize Docling's HybridChunker with the same tokenizer as embedding model
        tokenizer = HuggingFaceTokenizer(
            tokenizer=AutoTokenizer.from_pretrained(model_name),
            max_tokens=settings.TARGET_CHUNK_SIZE_IN_TOKENS,
        )

        self.chunker = HybridChunker(
            tokenizer=tokenizer,
            merge_peers=True,
        )

    def chunk_docling_document(
        self, docling_doc: DoclingDocument
    ) -> List[ChunkWithPage]:
        """
        Chunks a DoclingDocument directly, preserving tables and structured content.
        This method works with documents from the extraction service.

        Args:
            docling_doc: The DoclingDocument from the extraction service.

        Returns:
            A list of ChunkWithPage objects containing text chunks and their page numbers.
        """
        chunk_iter = self.chunker.chunk(dl_doc=docling_doc)

        # Extract the contextualized text and page information from each chunk
        chunks = []
        for chunk in chunk_iter:
            # This ensures tables are serialized properly (markdown format by default)
            contextualized_text = self.chunker.contextualize(chunk=chunk)

            # Extract page number from the chunk's metadata
            page_number = None
            if chunk.meta.doc_items:
                # Get the page number from the first doc item's provenance
                for doc_item in chunk.meta.doc_items:
                    if doc_item.prov:
                        page_number = doc_item.prov[0].page_no
                        break

            chunks.append(
                ChunkWithPage(text=contextualized_text, page_number=page_number)
            )

        return chunks

    def chunk_text(self, text: str) -> List[str]:
        """
        Splits a given text into smaller chunks using Docling's hybrid chunker.
        This method properly handles tables and structured content.

        Args:
            text: The text to be chunked.

        Returns:
            A list of text chunks.
        """
        from docling_core.types.doc import DoclingDocument, TextItem
        from docling_core.types.doc.labels import DocItemLabel

        # Create a basic DoclingDocument
        doc = DoclingDocument(name="document")

        # Add the text as a single text item
        text_item = TextItem(text=text, label=DocItemLabel.TEXT)
        doc.texts.append(text_item)

        # Use the hybrid chunker to create chunks
        chunk_iter = self.chunker.chunk(dl_doc=doc)

        # Extract the contextualized text from each chunk
        chunks = []
        for chunk in chunk_iter:
            # Use the contextualize method to get the final text for embedding
            contextualized_text = self.chunker.contextualize(chunk=chunk)
            chunks.append(contextualized_text)

        return chunks

    def embed_chunks(self, chunks: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a list of text chunks.

        Args:
            chunks: A list of text chunks.

        Returns:
            A list of embedding vectors.
        """
        embeddings = self.embedding_model.embed_documents(chunks)
        return embeddings


# Vector store using Weaviate
class WeaviateService:
    def __init__(self):
        self.class_name = "DocumentChunk"
        self._client = None
        self._create_schema_if_not_exists()

    def _connect(self):
        if self._client is None:
            parsed_url = urlparse(settings.WEAVIATE_URL)
            self._client = weaviate.WeaviateClient(
                connection_params=weaviate.connect.ConnectionParams.from_params(
                    http_host=parsed_url.hostname,
                    http_port=parsed_url.port,
                    http_secure=parsed_url.scheme == "https",
                    grpc_host=parsed_url.hostname,
                    grpc_port=50051,
                    grpc_secure=False,
                ),
            )
            self._client.connect()
        return self._client

    def _close(self):
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close()

    def _create_schema_if_not_exists(self):
        with self:
            client = self._client
            if not client.collections.exists(self.class_name):
                client.collections.create(
                    name=self.class_name,
                    vectorizer_config=Configure.Vectorizer.none(),
                    properties=[
                        Property(name="tenant_id", data_type=DataType.TEXT),
                        Property(name="document_id", data_type=DataType.TEXT),
                        Property(name="content", data_type=DataType.TEXT),
                        Property(name="page_number", data_type=DataType.INT),
                        Property(name="original_filename", data_type=DataType.TEXT),
                    ],
                )

    def add_document_chunks(
        self, document: Document, chunks: List[ChunkWithPage], embeddings: list
    ):
        with self:
            collection = self._client.collections.get(self.class_name)
            with collection.batch.dynamic() as batch:
                for i, chunk_data in enumerate(chunks):
                    properties = {
                        "tenant_id": str(document.tenant.id),
                        "document_id": str(document.id),
                        "content": chunk_data.text,
                        "page_number": chunk_data.page_number,
                        "original_filename": document.original_filename,
                    }
                    batch.add_object(properties=properties, vector=embeddings[i])

    def __del__(self):
        self._close()


# DocumentProcessingService comprises (extraction, embedding generation, and storage in vector db - weaviate)
class DocumentProcessingService:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.extraction_service = ExtractionService()
        self.embedding_service = EmbeddingService()
        self.vector_store = WeaviateService()

    def process_document(self, document_id: str):
        doc: Document = Document.objects.get(id=document_id)

        try:
            doc.status = Document.ProcessingStatus.PROCESSING
            doc.save()

            file_path = Path(doc.original_file.path)
            markdown_path, image_dir, docling_doc = self.extraction_service.extract(
                file_path, self.tenant_id
            )

            pages = len(getattr(docling_doc, "pages", []))
            doc_metadata = {
                "extension": file_path.suffix.lower(),
                "source": "upload",
                "file_size": file_path.stat().st_size,
                "markdown_path": str(markdown_path),
                "image_dir_path": str(image_dir),
            }

            if docling_doc.origin:
                doc_metadata.update(
                    {
                        "mimetype": docling_doc.origin.mimetype,
                        "binary_hash": str(docling_doc.origin.binary_hash),
                    }
                )

            chunks_with_pages = self.embedding_service.chunk_docling_document(
                docling_doc
            )
            chunk_texts = [c.text for c in chunks_with_pages]
            embeddings = self.embedding_service.embed_chunks(chunk_texts)

            with self.vector_store:
                self.vector_store.add_document_chunks(
                    doc, chunks_with_pages, embeddings
                )

            doc.status = Document.ProcessingStatus.COMPLETED
            doc.processed_at = timezone.now()
            doc.page_count = pages
            doc.metadata = doc_metadata
            doc.save()
        except Exception as e:
            doc.status = Document.ProcessingStatus.FAILED
            doc.error_message = str(e)
            doc.save()
            doc.original_file.delete(save=False)
            raise e

    def __del__(self):
        """Ensure Weaviate client is closed when the service is destroyed."""
        if hasattr(self, "vector_store"):
            self.vector_store._close()
