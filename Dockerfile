FROM python:3.9-alpine
LABEL maintainer sftan@icloud.com

WORKDIR /app

# create and activate python virtual environment
RUN python3 -m venv venv
RUN source venv/bin/activate

# install all the neccesary python packages into
# virtual environment
COPY requirements.txt .
RUN apk add --no-cache --virtual .build-deps \
    python3-dev \
    build-base \
    librdkafka-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del --no-cache .build-deps 

# install additional run-time library
# librdkafka is required by Confluent-Kafka python package
RUN apk add librdkafka

# copy application files into the working directory
COPY kafka_rest.py .

EXPOSE 8888
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8888", "kafka_rest:app"]
