FROM python:3.11-slim

WORKDIR /app

# EasyOCR needs these system libraries for image processing
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the EasyOCR model so the first container run isn't slow
RUN python -c "import easyocr; easyocr.Reader(['en'], gpu=False)"

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
