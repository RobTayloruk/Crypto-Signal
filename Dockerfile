FROM python:3.11-slim

WORKDIR /workspace
COPY requirements.txt ./
COPY app/ ./app/
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app/dashboard.py", "--server.address=0.0.0.0", "--server.port=8501"]
