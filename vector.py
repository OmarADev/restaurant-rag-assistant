from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from PIL import Image
from pypdf import PdfReader

import os
import pandas as pd
import pytesseract
import glob

# -----------------------------------------------
# CONFIGURATION — swap these to change restaurant
# -----------------------------------------------
RESTAURANT_NAME = "Pizza Palace"
CSV_FILENAME = "realistic_restaurant_reviews.csv"   # customer reviews
# Any .pdf files in the project directory are auto-loaded as menu/docs
# Any .png/.jpg images are loaded via the hardcoded image_documents list below
# -----------------------------------------------

script_dir = os.path.dirname(os.path.abspath(__file__))


# -------------------------------
# LOAD CSV DATA (Customer Reviews)
# -------------------------------

csv_path = os.path.join(script_dir, CSV_FILENAME)
print(f"Loading CSV from: {csv_path}")
df = pd.read_csv(csv_path)
print(f"Loaded {len(df)} reviews from CSV")


# -------------------------------
# LOAD PDF DATA (Menu / Docs)
# -------------------------------

pdf_files = glob.glob(os.path.join(script_dir, "*.pdf"))
print(f"Found {len(pdf_files)} PDF files")

pdf_documents = []
for pdf_file in pdf_files:
    print(f"  Loading: {os.path.basename(pdf_file)}")
    reader = PdfReader(pdf_file)
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        pdf_documents.append({
            "content": text,
            "source": os.path.basename(pdf_file),
            "page": page_num + 1
        })

print(f"Loaded {len(pdf_documents)} pages from PDFs")


# -------------------------------
# LOAD IMAGE DATA
# -------------------------------
# Note: image ingestion currently uses manually extracted text.
# Full Tesseract OCR support is planned for a future update.
# To add a new image, append an entry to image_documents below.

image_documents = [
    {
        "content": (
            "Student Discount: 10% off the total bill with a valid college ID. "
            "Offer applies all day, every day, for groups up to 4 students."
        ),
        "source": "student_discount.png",
    }
]

print(f"Loaded {len(image_documents)} image document(s)")


# -------------------------------
# EMBEDDINGS
# -------------------------------

embeddings = OllamaEmbeddings(model="all-minilm")


# -------------------------------
# VECTOR DATABASE (Chroma)
# -------------------------------

db_location = os.path.join(script_dir, "chrome_langchain_db")
add_documents = not os.path.exists(db_location)

if add_documents:
    print("Creating vector database...")

    documents = []
    ids = []
    doc_id = 0

    # CSV reviews
    for i, row in df.iterrows():
        document = Document(
            page_content=row["Title"] + " " + row["Review"],
            metadata={"rating": row["Rating"], "date": row["Date"], "source": "CSV"},
            id=str(doc_id)
        )
        ids.append(str(doc_id))
        documents.append(document)
        doc_id += 1

    # PDF pages
    for pdf_doc in pdf_documents:
        document = Document(
            page_content=pdf_doc["content"],
            metadata={"source": "PDF", "filename": pdf_doc["source"], "page": pdf_doc["page"]},
            id=str(doc_id)
        )
        ids.append(str(doc_id))
        documents.append(document)
        doc_id += 1

    # Image text
    for img_doc in image_documents:
        document = Document(
            page_content=img_doc["content"],
            metadata={"source": "IMAGE", "filename": img_doc["source"]},
            id=str(doc_id)
        )
        ids.append(str(doc_id))
        documents.append(document)
        doc_id += 1

    vector_store = Chroma(
        collection_name="restaurant_reviews",
        persist_directory=db_location,
        embedding_function=embeddings
    )
    vector_store.add_documents(documents=documents, ids=ids)
    print(f"Vector database created with {len(documents)} documents")

else:
    print("Loading existing vector database...")
    vector_store = Chroma(
        collection_name="restaurant_reviews",
        persist_directory=db_location,
        embedding_function=embeddings
    )


# -------------------------------
# RETRIEVER
# -------------------------------

retriever = vector_store.as_retriever(
    search_kwargs={"k": 5}
)
