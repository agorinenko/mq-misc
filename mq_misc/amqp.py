"""
Базовое API для работы с RabbitMQ
"""
import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any, Optional, Union

import aio_pika
from mq_misc.errors import AdapterError


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
                 loop: Optional[asyncio.AbstractEventLoop] = asyncio.get_event_loop()):

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

    async def declare_queue(self, **kwargs) -> aio_pika.Queue:
        """
        Определение очереди
        """
        if self.channel is None:
            raise AdapterError("Connection is not established: channel is none")

        queue_kwargs = dict(
            durable=kwargs.get('durable', None),
            exclusive=kwargs.get('exclusive', False),
            passive=kwargs.get('passive', False),
            auto_delete=kwargs.get('auto_delete', False),
            arguments=kwargs.get('arguments', None),
            timeout=kwargs.get('timeout', None),
            robust=kwargs.get('robust', True)
        )

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

    @abstractmethod
    async def validate_message(self, message_json: Any) -> bool:
        """
        Валидация сообщения на основе схемы
        """
        raise NotImplementedError("Not implemented validate_message method")

    async def create_consume_connection(self, robust: Optional[bool] = True,
                                        prefetch_count: Optional[int] = 0,
                                        **kwargs) -> aio_pika.Connection:
        """
        Создание подключения для потребителя
        """
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

                validate_message_result = await self.validate_message(message_json)
                if not validate_message_result:
                    raise AdapterError("Message did not pass validation")

                await self.process_message(message_json, message)
            except Exception as ex:
                await self._on_handle_delivery_error(ex, message)

    async def _on_handle_delivery_error(self, ex: Exception,
                                        raw_message: aio_pika.IncomingMessage) -> None:
        """
        Произошла ошибка при обработке полученного сообщения
        """
        self.logger.error(ex, exc_info=True)


class Publisher(BaseAdapter):
    """
    Базовый издатель очереди сообщений
    """

    async def publish(self, message: Union[str, dict], **kwargs) -> None:
        """
        Создание подключения для издателя
        """
        if self.channel is None:
            raise AdapterError("Connection is not established: channel is none")

        message_body = encode_message(message)

        await self.channel.default_exchange.publish(
            aio_pika.Message(
                message_body,
                content_type="application/json",
                **kwargs
            ),
            routing_key=self.queue_name,
        )


class ReplyToConsumer(BaseConsumer, ABC):
    """
    Reply-To потребитель
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
        """
        if self.channel is None:
            raise AdapterError("Connection is not established: channel is none")

        self.futures = dict()
        self.queue = await self.channel.declare_queue(exclusive=True)

        return self.queue

    async def publish(self, message: dict):
        """
        После начала чтения очереди вызываем publish сообщения
        """
        correlation_id = str(uuid.uuid4())

        future = self.loop.create_future()

        self.futures[correlation_id] = future, message

        await self._publish(message, correlation_id)

        return await asyncio.wait_for(future, timeout=self.timeout)

    @abstractmethod
    async def _publish(self, message: dict, correlation_id: str) -> Any:
        """
        После начала чтения очереди вызываем publish сообщения
        """
        raise NotImplementedError("Not implemented after_consume method")

    async def _handle_delivery(self, message: aio_pika.IncomingMessage) -> None:
        correlation_id = message.correlation_id
        if correlation_id not in self.futures:
            raise AdapterError(f"Correlation id '{correlation_id}' is not trusted")

        await super()._handle_delivery(message)

        future, message = self.futures.pop(correlation_id)
        future.set_result(True)
