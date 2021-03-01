import asyncio
from unittest.mock import AsyncMock

import aio_pika

from mq_misc.amqp import BaseConsumer, Publisher, ReplyToConsumer

url = f"amqp://guest:guest@localhost:5672/"
queue_name = "test"


class ResponseConsumer(BaseConsumer):
    async def process_message(self, body: dict, raw_message: aio_pika.IncomingMessage) -> None:
        await self.publish_response(raw_message, {"response": True})


class RequestConsumer(ReplyToConsumer):
    async def process_message(self, body: dict, raw_message: aio_pika.IncomingMessage) -> None:
        pass


class TestConsumer(BaseConsumer):
    async def process_message(self, body: dict, raw_message: aio_pika.IncomingMessage) -> None:
        pass


async def test_consumer(loop):
    consumer = TestConsumer(url, queue_name, loop=loop)
    consumer.process_message = AsyncMock(return_value=None)
    await consumer.create_consume_connection()

    publisher = Publisher(url, queue_name, loop)
    await publisher.create_connection()
    await publisher.publish({'success': True})
    await publisher.publish({'success': False})

    await asyncio.sleep(1)

    assert consumer.process_message.call_count == 2


async def test_reply_to_consumer(loop):
    reply_to_queue_name = "reply_to_test"

    response_consumer = ResponseConsumer(url, queue_name, loop=loop)
    await response_consumer.create_consume_connection()

    publisher = Publisher(url, queue_name, loop)
    await publisher.create_connection()

    request_consumer = RequestConsumer(url, reply_to_queue_name, loop=loop)
    request_consumer.process_message = AsyncMock(return_value=None)
    await request_consumer.create_consume_connection()

    await request_consumer.publish({'request': True}, publisher)
    await request_consumer.publish({'request': True}, publisher)

    await asyncio.sleep(1)

    assert request_consumer.process_message.call_count == 2
