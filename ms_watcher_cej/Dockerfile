FROM python:3.12.11-slim-bookworm

WORKDIR /home/app

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
     libaio1 gcc g++ curl zlib1g libexpat1 \
 && rm -rf /var/lib/apt/lists/*

COPY . /home/app

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

EXPOSE 5090
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5090"]

#uvicorn main:app --host 0.0.0.0 --port 5000