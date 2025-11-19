FROM arm64v8/python:3.11-bullseye

RUN apt-get update && apt-get install -y  --fix-missing \
    build-essential \
    libpq-dev \
    libffi-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN python3 manage.py collectstatic --no-input

EXPOSE 8000

CMD ["gunicorn", "--workers=4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "api.asgi:application", "--log-level","debug"]