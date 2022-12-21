FROM python:3.9.1-slim

WORKDIR /code

RUN apt-get update \
    && apt-get -y install libpq-dev gcc musl-dev git

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt
RUN pip install av

COPY . /code

WORKDIR src
CMD ["python3", "-m", "movi_hmdb_off"]