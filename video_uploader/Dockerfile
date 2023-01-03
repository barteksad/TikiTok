FROM python:3.11.1-slim

WORKDIR /code

RUN apt-get update \
    && apt-get -y install libpq-dev gcc musl-dev

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . /code

ENV GOOGLE_APPLICATION_CREDENTIALS="firebase-admin.json"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]