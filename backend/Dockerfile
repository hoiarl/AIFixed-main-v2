FROM python:3.11-slim

WORKDIR /code

# Default model cache locations (can be overridden via environment)
ENV HF_HOME=/models_cache/huggingface \
    TRANSFORMERS_CACHE=/models_cache/huggingface/transformers \
    SENTENCE_TRANSFORMERS_HOME=/models_cache/sentence-transformers \
    TORCH_HOME=/models_cache/torch

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN npm install --prefix /code/pptx_worker

# Ensure cache directories exist with sane permissions
RUN mkdir -p /models_cache/huggingface/transformers \
    /models_cache/sentence-transformers \
    /models_cache/torch \
    /code/storage/templates && \
    chmod -R 777 /models_cache /code/storage

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
