"""
Базовое API для работы с RabbitMQ
"""
import asyncio
import json
import logging
import pprint
import uuid
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, Optional, Union, Callable, Dict, Awaitable

import aio_pika
from aio_pika import ExchangeType

from mq_misc.errors import AdapterError


@asynccontextmanager
async def create_weak_publisher(*args, **kwargs):
    """ Инициализация издателя """
    publisher_obj = Publisher(*args, **kwargs)
    await publisher_obj.create_connection(robust=False)
    try:
        yield publisher_obj
    finally:
        await publisher_obj.close()


def encode_message(message: Union[str, dict]) -> bytes:
    """
    Кодирование сообщения
    """
    if isinstance(message, str):
        message = json.loads(message)

    return json.dumps(message).encode()


def decode_message(message: aio_pika.IncomingMessage) -> Any:
    """
    Декодирование сообщения
    """
    message_data = message.body
    data = json.loads(message_data)
    return data


class BaseAdapter(ABC):
    """
    Базовый адаптер очереди сообщений
    """

    def __init__(self, url: str,
                 queue_name: Optional[str] = None,
                 exchange_name: Optional[str] = None,
                 exchange_type: Union[ExchangeType, str] = ExchangeType.DIRECT,
                 loop: Optional[asyncio.AbstractEventLoop] = None):
        if loop is None:
            loop = asyncio.get_event_loop()

        self.loop = loop
        self.url = url
        self.queue_name = queue_name

        self.connection = None
        self.channel = None
        self.exchange = None
        self.queue = None

        self.logger = logging.getLogger(__name__)

        self.exchange_name = exchange_name
        self.exchange_type = exchange_type

    async def create_connection(self,
                                robust: Optional[bool] = True,
                                prefetch_count: Optional[int] = 0) -> aio_pika.Connection:
        """
        Создание подключения
        """
        if self.connection is None:
            if robust:
                self.connection = await aio_pika.connect_robust(
                    self.url,
                    loop=self.loop)
            else:
                self.connection = await aio_pika.connect(
                    self.url,
                    loop=self.loop)

        if self.channel is None:
            self.channel = await self.connection.channel()

        self.exchange = self.channel.default_exchange

        await self.channel.set_qos(prefetch_count=prefetch_count)

        return self.connection

    async def declare_exchange(self, **kwargs) -> aio_pika.Exchange:
        if not self.channel:
            raise AdapterError('Connection is not established: channel is none')

        if not self.exchange_name:
            raise ValueError('Exchange name is none or empty')

        exchange_kwargs = dict(
            durable=kwargs.get('durable'),
            internal=kwargs.get('internal', False),
            passive=kwargs.get('passive', False),
            auto_delete=kwargs.get('auto_delete', False),
            arguments=kwargs.get('arguments'),
            timeout=kwargs.get('timeout')
        )
        if 'robust' in kwargs:
            exchange_kwargs['robust'] = kwargs['robust']

        self.logger.debug('declare_exchange:\n%s', pprint.pformat(exchange_kwargs))

        self.exchange = await self.channel.declare_exchange(self.exchange_name, self.exchange_type, **exchange_kwargs)

        return self.exchange

    async def declare_queue(self, **kwargs) -> aio_pika.Queue:
        """
        Определение очереди
        """
        if not self.channel:
            raise AdapterError('Connection is not established: channel is none')

        queue_kwargs = dict(
            durable=kwargs.get('durable'),
            exclusive=kwargs.get('exclusive', False),
            passive=kwargs.get('passive', False),
            auto_delete=kwargs.get('auto_delete', False),
            arguments=kwargs.get('arguments'),
            timeout=kwargs.get('timeout')
        )
        if 'robust' in kwargs:
            queue_kwargs['robust'] = kwargs['robust']

        self.logger.debug('declare_queue:\n%s', pprint.pformat(queue_kwargs))

        self.queue = await self.channel.declare_queue(self.queue_name, **queue_kwargs)

        return self.queue

    async def close_channel(self) -> None:
        """
        Закрытие канала
        """
        if self.channel is not None:
            await self.channel.close()

    async def close(self) -> None:
        """
        Закрытие подключения
        """
        await self.close_channel()

        if self.connection is not None:
            await self.connection.close()


class BaseConsumer(BaseAdapter, ABC):
    """
    Базовый потребитель очереди сообщений
    """

    @abstractmethod
    async def process_message(self, body: dict, raw_message: aio_pika.IncomingMessage) -> None:
        """
        Обработка подготовленного и провалидированного Json сообщения
        """
        raise NotImplementedError("Not implemented process_message method")

    async def create_consume_connection(self, robust: Optional[bool] = True,
                                        prefetch_count: Optional[int] = 0,
                                        **kwargs) -> aio_pika.Connection:
        """
        Создание подключения для потребителя
        """
        if robust:
            kwargs['robust'] = True
        await self.create_connection(robust=robust, prefetch_count=prefetch_count)
        await self.declare_queue(**kwargs)

        consume_kwargs = dict(
            no_ack=kwargs.get('no_ack', False)
        )

        if self.queue is None:
            raise AdapterError("Connection is not established: queue is none")

        await self.queue.consume(self._handle_delivery, **consume_kwargs)

        return self.connection

    async def _handle_delivery(self, message: aio_pika.IncomingMessage) -> None:
        """
        Обработка полученного сообщения
        """
        async with message.process():
            try:
                message_json = decode_message(message)

                await self.process_message(message_json, message)
            except Exception as ex:
                await self._on_handle_delivery_error(ex, message)

    async def _on_handle_delivery_error(self, ex: Exception,
                                        raw_message: aio_pika.IncomingMessage) -> None:
        """
        Произошла ошибка при обработке полученного сообщения
        """
        self.logger.error(ex, exc_info=True)

    async def publish_response(self, incoming_message: aio_pika.IncomingMessage, message: Union[str, dict]):
        if self.channel is None:
            raise AdapterError("Connection is not established: channel is none")

        message_body = encode_message(message)

        await self.channel.default_exchange.publish(
            aio_pika.Message(
                message_body,
                content_type="application/json",
                correlation_id=incoming_message.correlation_id
            ),
            routing_key=incoming_message.reply_to,
        )


class Publisher(BaseAdapter):
    """
    Издатель очереди сообщений
    """

    async def publish(self, message: Union[str, dict], **kwargs) -> None:
        """
        Создание подключения для издателя
        """
        if self.channel is None:
            raise AdapterError('Connection is not established: channel is none')

        if self.exchange is None:
            raise AdapterError('Connection is not established: exchange is none')

        message_body = encode_message(message)

        routing_key = kwargs.pop('routing_key', self.queue_name)

        await self.exchange.publish(
            aio_pika.Message(
                message_body,
                content_type='application/json',
                **kwargs
            ),
            routing_key=routing_key,
        )


class ReplyToConsumer(BaseConsumer, ABC):
    """
    Reply-To потребитель,
    который может публиковать сообщение в произвольную очередь с указанием того, куда нужно вернуть ответ
    """
    futures = None

    @property
    def timeout(self) -> Optional[Union[int, float]]:
        """
        Таймаут ожидания выполнения future на получения ответа в секундах.
        Может быть None, float или int.
        Если таймаут None, то ожидание длится до выполнения future.
        """
        return None

    async def declare_queue(self, **kwargs) -> aio_pika.Queue:
        """
        Определение очереди
        :param kwargs:
        :return:
        """
        if self.channel is None:
            raise AdapterError("Connection is not established: channel is none")

        self.futures = dict()
        self.queue = await self.channel.declare_queue(exclusive=True)

        return self.queue

    async def publish(self, message: dict, publisher: Publisher):
        """
        Публикация сообщения в очередь
        :param message: сообщение
        :param publisher: издатель
        :return:
        """
        correlation_id = str(uuid.uuid4())

        future = self.loop.create_future()

        self.futures[correlation_id] = future, message

        await self._publish(message, correlation_id, publisher)

        return await asyncio.wait_for(future, timeout=self.timeout)

    async def _publish(self, message: dict, correlation_id: str, publisher: Publisher) -> None:
        """
        Публикация сообщения в произвольную очередь с указанием reply_to очереди для ответа
        :param message: сообщение
        :param correlation_id: идентификатор сообщения
        :param publisher: издатель
        :return:
        """
        await publisher.publish(message,
                                correlation_id=correlation_id,
                                reply_to=self.queue.name)

    async def _handle_delivery(self, message: aio_pika.IncomingMessage) -> None:
        correlation_id = message.correlation_id
        if correlation_id not in self.futures:
            raise AdapterError(f"Correlation id '{correlation_id}' is not trusted")

        await super()._handle_delivery(message)

        future, message = self.futures.pop(correlation_id)
        future.set_result(True)
