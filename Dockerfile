FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ scripts/
COPY sql/ sql/
COPY data/raw/ data/raw/

RUN mkdir -p data/staging data/warehouse

CMD ["sh", "-c", "python scripts/01_generate_data.py && python scripts/02_transform.py && python scripts/03_load_warehouse.py"]