FROM python:3.12-slim

WORKDIR /app

# Removed software-properties-common from this command
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/chrisbrunet/activedata.git .

COPY .streamlit/secrets.toml /app/.streamlit/secrets.toml

RUN pip install -r requirements.txt

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "myApp.py", "--server.port=8501", "--server.address=0.0.0.0"]