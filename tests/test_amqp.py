import asyncio
import os
import uuid
from unittest.mock import AsyncMock

import aio_pika

from mq_misc.amqp import BaseConsumer, ReplyToConsumer, create_weak_publisher

url = os.environ.get('MQ_MISC_TEST_AMQP_URL', 'amqp://guest:guest@localhost:5672/')


def make_queue_name() -> str:
    """Уникальное имя очереди, чтобы тесты не зависели от состояния брокера."""
    return f'test-{uuid.uuid4()}'


class ResponseConsumer(BaseConsumer):
    async def process_message(self, body: dict, raw_message: aio_pika.IncomingMessage,
                              message_id=None, **kwargs) -> None:
        await self.publish_response(raw_message, {'response': True})


class RequestConsumer(ReplyToConsumer):
    @property
    def timeout(self) -> int:
        """Таймаут ожидания ответа в тестах, чтобы падать вместо зависания."""
        return 5

    async def process_message(self, body: dict, raw_message: aio_pika.IncomingMessage,
                              message_id=None, **kwargs) -> None:
        pass


class MyTestConsumer(BaseConsumer):
    async def process_message(self, body: dict, raw_message: aio_pika.IncomingMessage,
                              message_id=None, **kwargs) -> None:
        pass


async def test_consumer():
    queue_name = make_queue_name()
    consumer = MyTestConsumer(url, queue_name)
    consumer.process_message = AsyncMock(return_value=None)
    await consumer.create_consume_connection(robust=False, durable=True, auto_delete=True)

    try:
        async with create_weak_publisher(url, queue_name) as publisher:
            await publisher.publish({'success': True})
            await publisher.publish({'success': False})

        await asyncio.sleep(1)

        assert consumer.process_message.call_count == 2
    finally:
        await consumer.close()


async def test_reply_to_consumer():
    queue_name = make_queue_name()
    reply_to_queue_name = make_queue_name()

    response_consumer = ResponseConsumer(url, queue_name)
    await response_consumer.create_consume_connection(robust=False, durable=True, auto_delete=True)

    try:
        async with create_weak_publisher(url, queue_name) as publisher:
            request_consumer = RequestConsumer(url, reply_to_queue_name)
            request_consumer.process_message = AsyncMock(return_value=None)
            await request_consumer.create_consume_connection(robust=False)

            try:
                await request_consumer.publish({'request': True}, publisher)
                await request_consumer.publish({'request': True}, publisher)

                await asyncio.sleep(1)

                assert request_consumer.process_message.call_count == 2
            finally:
                await request_consumer.close()
    finally:
        await response_consumer.close()


async def test_connection():
    """ Проверка соединения """
    async with create_weak_publisher(url) as publisher:
        assert not publisher.connection.is_closed
