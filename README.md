# 🍽️ Restaurant RAG Assistant

A Retrieval-Augmented Generation (RAG) chatbot that answers questions about real local restaurants using only their actual data. Fetches restaurant information from OpenStreetMap, supports PDF menus and image-based menus via OCR, and grounds every answer in the restaurant's own documents.

---

## What It Does

- Fetches real restaurant data (name, cuisine, hours, address, phone, website) from OpenStreetMap — no API key needed
- Supports uploading a restaurant's PDF menu or a photo of their menu (processed via EasyOCR)
- Answers questions grounded strictly in that restaurant's documents — no hallucination
- Shows which document type each answer came from (info, menu, image)
- Supports multiple restaurants across multiple cities via a sidebar selector

---

## Demo Flow

```
1. Run fetch_restaurant.py → enter a city
2. App fetches nearby restaurants and saves their data
3. Launch the Streamlit app
4. Select a restaurant from the sidebar
5. Ask questions — answers reference only that restaurant's data
```

---

## Tech Stack

| Component | Tool |
|-----------|------|
| LLM | Llama 3.2 via [Ollama](https://ollama.com) (runs locally) |
| Embeddings | `all-minilm` via Ollama |
| Vector Database | [Chroma](https://www.trychroma.com/) (one per restaurant) |
| RAG Framework | [LangChain](https://www.langchain.com/) |
| UI | [Streamlit](https://streamlit.io/) |
| Restaurant Data | [OpenStreetMap](https://www.openstreetmap.org/) via Overpass API |
| OCR | [EasyOCR](https://github.com/JaidedAI/EasyOCR) (no external binary needed) |
| PDF Parsing | pypdf |

---

## Setup

### Option A — Docker (recommended)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
git clone https://github.com/OmarADev/restaurant-rag-assistant.git
cd restaurant-rag-assistant
docker compose up --build
```

On first run, pull the models into the Ollama container:

```bash
docker exec -it ollama ollama pull llama3.2
docker exec -it ollama ollama pull all-minilm
```

Then fetch restaurant data:

```bash
docker exec -it rag-app python fetch_restaurant.py
# Enter a city name when prompted (e.g. Berlin, Munich, London)
```

Open **http://localhost:8501**. Restaurant data is stored in `./data/` on your machine and persists across restarts.

---

### Option B — Local Python

#### 1. Install Ollama and pull models

```bash
# Install Ollama: https://ollama.com/download
ollama pull llama3.2
ollama pull all-minilm
```

#### 2. Clone and install dependencies

```bash
git clone https://github.com/OmarADev/restaurant-rag-assistant.git
cd restaurant-rag-assistant

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

#### 3. Fetch restaurant data

```bash
python fetch_restaurant.py
# Enter a city name when prompted (e.g. Berlin, Munich, London)
```

#### 4. (Optional) Add a menu

Drop a PDF or image of the menu into the restaurant's data folder:
```
data/<city>/<restaurant_slug>/menu.pdf
data/<city>/<restaurant_slug>/menu.png
```
Delete the `.vector_db` folder inside that restaurant's directory to force a rebuild on next launch.

#### 5. Launch the app

```bash
streamlit run app.py
```

---

## Project Structure

```
restaurant-rag-assistant/
├── app.py                  # Streamlit UI + LangChain chain
├── vector.py               # Document loading, EasyOCR, Chroma setup
├── fetch_restaurant.py     # Fetches real restaurants from OpenStreetMap
├── Dockerfile              # App container image
├── docker-compose.yml      # Orchestrates app + Ollama containers
├── requirements.txt
├── .gitignore
└── data/                   # Auto-created by fetch_restaurant.py
    └── berlin/
        └── some_restaurant/
            ├── info.json       # Restaurant info
            ├── menu.pdf        # Optional: PDF menu
            ├── menu.png        # Optional: menu photo (processed via OCR)
            └── .vector_db/     # Auto-generated, gitignored
```

---

## Architecture

```
User question
     │
     ▼
Retriever (Chroma — restaurant-specific)
     │
     ▼
Top 5 relevant document chunks
  [INFO] [MENU (PDF)] [IMAGE]
     │
     ▼
LangChain prompt (chunks + question + strict rules)
     │
     ▼
Llama 3.2 (local via Ollama)
     │
     ▼
Answer + source indicator in UI
```

---

## Notes

- All inference runs locally — no OpenAI key or internet needed after setup
- EasyOCR downloads its model (~100MB) on first use
- Each restaurant's vector DB is stored inside its own data folder and gitignored
- OpenStreetMap data quality varies by city — larger cities have more complete data
