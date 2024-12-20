FROM python:3.12

WORKDIR /app

RUN pip install pydicom pandas

COPY dcm_crawler.py .