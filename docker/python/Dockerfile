FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r --no-cache-dir requirements.txt

COPY src/ /app/src

CMD ["python", "-m", "src.main"]