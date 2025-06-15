FROM python:3.13-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache \
    gcc \
    python3-dev \
    musl-dev \
    linux-headers

WORKDIR /app

COPY salon_manager/requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "salon_manager/manage.py", "runserver", "0.0.0.0:8000"]
