FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e .
EXPOSE 8000 8501
CMD sh -c "uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8000} & streamlit run app.py --server.port 8501 --server.headless true --server.address 0.0.0.0 && wait"
