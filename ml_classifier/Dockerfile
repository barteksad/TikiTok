FROM bitnami/pytorch
USER root
WORKDIR /code

COPY model.txt model.txt
COPY requirements.txt requirements.txt

RUN pip install av
RUN pip install -r requirements.txt

RUN pip install einops
RUN pip install fvcore
ENV PYTHONUNBUFFERED=1

COPY . /code

WORKDIR src
CMD ["python3", "-m", "main"]