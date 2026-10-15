FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./
COPY data/ ./data/
RUN useradd -u 10001 appuser && chown -R appuser /srv
USER 10001
EXPOSE 8000
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
