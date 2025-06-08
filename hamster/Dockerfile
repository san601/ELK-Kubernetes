FROM python:3.9-alpine

WORKDIR /app

RUN apk update && \
    apk add --no-cache build-base libffi-dev openssl-dev sqlite

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8888

CMD ["gunicorn", "--workers", "4", "--bind", "0.0.0.0:8888", "app:app"]