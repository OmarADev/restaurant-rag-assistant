# vector.py
# Handles document loading, embedding, and vector database management.
# Supports JSON (restaurant info), PDF (menus), and images (EasyOCR).
# Each restaurant gets its own isolated Chroma collection.

import os
import json
import glob

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

import easyocr
from pypdf import PdfReader
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# EasyOCR reader — loaded once, reused across calls
# Set gpu=False since most machines won't have CUDA available
_ocr_reader = None

def get_ocr_reader():
    """Lazy-load EasyOCR reader to avoid slow startup when OCR isn't needed."""
    global _ocr_reader
    if _ocr_reader is None:
        print("Loading EasyOCR model (first run may download ~100MB)...")
        _ocr_reader = easyocr.Reader(["en"], gpu=False)
    return _ocr_reader


def load_json_doc(json_path):
    """Load restaurant info from a JSON file into a Document."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Format all fields into readable text for embedding
    lines = []
    field_labels = {
        "name": "Restaurant name",
        "cuisine": "Cuisine type",
        "opening_hours": "Opening hours",
        "phone": "Phone",
        "website": "Website",
        "address": "Address",
    }
    for key, label in field_labels.items():
        value = data.get(key, "Not available")
        lines.append(f"{label}: {value}")

    content = "\n".join(lines)
    return Document(
        page_content=content,
        metadata={"source": "INFO", "filename": os.path.basename(json_path)}
    )


def load_pdf_docs(pdf_path):
    """Extract text from each page of a PDF and return as Documents."""
    docs = []
    reader = PdfReader(pdf_path)
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            docs.append(Document(
                page_content=text,
                metadata={
                    "source": "MENU (PDF)",
                    "filename": os.path.basename(pdf_path),
                    "page": page_num + 1
                }
            ))
    return docs


def load_image_doc(image_path):
    """Extract text from an image using EasyOCR and return as a Document."""
    reader = get_ocr_reader()
    results = reader.readtext(image_path, detail=0)  # detail=0 returns text only
    text = " ".join(results).strip()

    if not text:
        print(f"  Warning: no text extracted from {os.path.basename(image_path)}")
        return None

    return Document(
        page_content=text,
        metadata={
            "source": "IMAGE",
            "filename": os.path.basename(image_path)
        }
    )


def build_vector_store(restaurant_folder):
    """
    Load all documents from a restaurant folder and build a Chroma vector store.
    Folder structure expected:
        data/<city>/<restaurant>/
            info.json         — restaurant info (required)
            *.pdf             — menus (optional)
            *.png / *.jpg     — images, e.g. menu photos (optional)
    """
    documents = []
    ids = []
    doc_id = 0

    print(f"\nLoading documents from: {restaurant_folder}")

    # Load info.json
    json_files = glob.glob(os.path.join(restaurant_folder, "info.json"))
    for path in json_files:
        doc = load_json_doc(path)
        documents.append(doc)
        ids.append(str(doc_id))
        doc_id += 1
        print(f"  Loaded info: {os.path.basename(path)}")

    # Load PDFs
    pdf_files = glob.glob(os.path.join(restaurant_folder, "*.pdf"))
    for path in pdf_files:
        docs = load_pdf_docs(path)
        for doc in docs:
            documents.append(doc)
            ids.append(str(doc_id))
            doc_id += 1
        print(f"  Loaded PDF: {os.path.basename(path)} ({len(docs)} pages)")

    # Load images via EasyOCR
    image_files = []
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        image_files.extend(glob.glob(os.path.join(restaurant_folder, ext)))

    for path in image_files:
        print(f"  Processing image: {os.path.basename(path)}")
        doc = load_image_doc(path)
        if doc:
            documents.append(doc)
            ids.append(str(doc_id))
            doc_id += 1

    if not documents:
        raise ValueError(f"No documents found in {restaurant_folder}")

    print(f"  Total documents: {len(documents)}")

    # Build Chroma vector store
    # Each restaurant gets its own DB folder to keep them isolated
    db_location = os.path.join(restaurant_folder, ".vector_db")
    embeddings = OllamaEmbeddings(model="all-minilm", base_url=OLLAMA_HOST)

    if os.path.exists(db_location):
        print("  Loading existing vector database...")
        vector_store = Chroma(
            collection_name="restaurant",
            persist_directory=db_location,
            embedding_function=embeddings
        )
    else:
        print("  Creating vector database...")
        vector_store = Chroma(
            collection_name="restaurant",
            persist_directory=db_location,
            embedding_function=embeddings
        )
        vector_store.add_documents(documents=documents, ids=ids)

    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    return retriever


def get_available_restaurants(data_dir="data"):
    """
    Scan the data/ directory and return all available restaurants.
    Returns a dict: { "City > Restaurant Name": folder_path }
    """
    options = {}
    if not os.path.exists(data_dir):
        return options

    for city in sorted(os.listdir(data_dir)):
        city_path = os.path.join(data_dir, city)
        if not os.path.isdir(city_path):
            continue
        for restaurant in sorted(os.listdir(city_path)):
            r_path = os.path.join(city_path, restaurant)
            if not os.path.isdir(r_path):
                continue
            # Only show folders that have an info.json
            if os.path.exists(os.path.join(r_path, "info.json")):
                # Load name from JSON for display
                try:
                    with open(os.path.join(r_path, "info.json")) as f:
                        info = json.load(f)
                    display_name = f"{city.replace('_', ' ').title()} › {info.get('name', restaurant)}"
                except Exception:
                    display_name = f"{city} › {restaurant}"
                options[display_name] = r_path

    return options
