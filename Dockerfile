FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .
EXPOSE 8000 8501

# SERVICE_MODE: "api" = FastAPI only, "ui" = Streamlit only, unset = both (docker-compose local)
CMD sh -c "\
  if [ \"$SERVICE_MODE\" = 'api' ]; then \
    uvicorn server.main:app --host 0.0.0.0 --port \${PORT:-8000}; \
  elif [ \"$SERVICE_MODE\" = 'ui' ]; then \
    streamlit run app.py --server.port \${PORT:-8501} --server.headless true --server.address 0.0.0.0; \
  else \
    uvicorn server.main:app --host 0.0.0.0 --port \${PORT:-8000} & \
    streamlit run app.py --server.port 8501 --server.headless true --server.address 0.0.0.0 & \
    wait; \
  fi"
