FROM python:3.9.1-slim

WORKDIR /code

RUN apt-get update \
    && apt-get -y install libpq-dev gcc musl-dev git

COPY model.txt model.txt

COPY requirements.txt requirements.txt

RUN pip install av
RUN pip install --no-cache-dir  -r model.txt
RUN pip install --no-cache-dir  -r requirements.txt


COPY . /code

WORKDIR src
CMD ["python3", "-m", "main"]