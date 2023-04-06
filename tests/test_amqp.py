import asyncio
from unittest.mock import AsyncMock

import aio_pika

from mq_misc.amqp import BaseConsumer, ReplyToConsumer, create_weak_publisher

url = 'amqp://guest:guest@localhost:5672/'
queue_name = 'test'


class ResponseConsumer(BaseConsumer):
    async def process_message(self, body: dict, raw_message: aio_pika.IncomingMessage) -> None:
        await self.publish_response(raw_message, {'response': True})


class RequestConsumer(ReplyToConsumer):
    async def process_message(self, body: dict, raw_message: aio_pika.IncomingMessage) -> None:
        pass


class MyTestConsumer(BaseConsumer):
    async def process_message(self, body: dict, raw_message: aio_pika.IncomingMessage) -> None:
        pass


async def test_consumer():
    consumer = MyTestConsumer(url, queue_name)
    consumer.process_message = AsyncMock(return_value=None)
    await consumer.create_consume_connection(robust=False)

    async with create_weak_publisher(url, queue_name) as publisher:
        await publisher.publish({'success': True})
        await publisher.publish({'success': False})

    await asyncio.sleep(1)

    assert consumer.process_message.call_count == 2


async def test_reply_to_consumer():
    reply_to_queue_name = "reply_to_test"

    response_consumer = ResponseConsumer(url, queue_name)
    await response_consumer.create_consume_connection(robust=False)

    async with create_weak_publisher(url, queue_name) as publisher:
        request_consumer = RequestConsumer(url, reply_to_queue_name)
        request_consumer.process_message = AsyncMock(return_value=None)
        await request_consumer.create_consume_connection(robust=False)

        await request_consumer.publish({'request': True}, publisher)
        await request_consumer.publish({'request': True}, publisher)

        await asyncio.sleep(1)

        assert request_consumer.process_message.call_count == 2
