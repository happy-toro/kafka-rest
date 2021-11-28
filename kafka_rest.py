import uvicorn
import json
from os import environ
from time import time
from threading import Thread
from fastapi import (FastAPI,
                     HTTPException,
                     status)
from pydantic import BaseModel
from confluent_kafka import (Producer as KafkaProducer,
                             KafkaException)


class Producer:
    def __init__(self, config):
        self._producer = KafkaProducer(config)
        self._cancelled = False
        self._poll_thread = Thread(target=self._poll_loop)
        self._poll_thread.start()

    def _poll_loop(self):
        while not self._cancelled:
            self._producer.poll(0.1)

    def close(self):
        self._cancelled = True
        self._poll_thread.join()

    def produce(self, topic, value, on_delivery=None):
        self._producer.produce(topic, value, on_delivery=on_delivery)


class Msg(BaseModel):
    topic: str
    value: dict


app = FastAPI()

BOOTSTRAP_SERVERS = environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')
config = {"bootstrap.servers": BOOTSTRAP_SERVERS}
producer = None


@app.on_event("startup")
async def startup_event():
    global producer
    producer = Producer(config)


@app.on_event("shutdown")
def shutdown_event():
    producer.close()


@app.post("/produce", status_code=status.HTTP_202_ACCEPTED)
async def produce_message(msg: Msg):
    try:
        producer.produce(topic=msg.topic, value=json.dumps(msg.value, default=str))
        return {"timestamp": time()}
    except KafkaException as ex:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=ex.args[0].str())


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8888)
