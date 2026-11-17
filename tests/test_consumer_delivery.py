import asyncio
import logging

from mq_misc.amqp import BaseConsumer


class FakeProcessContext:
    """Асинхронный контекстный менеджер обработки сообщения."""

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


class FakeIncomingMessage:
    """Минимальная заглушка aio_pika.IncomingMessage для unit-тестов."""

    def __init__(self, body: bytes, routing_key: str = 'test.route', redelivered: bool = False):
        self.body = body
        self.body_size = len(body)
        self.routing_key = routing_key
        self.redelivered = redelivered

    def process(self, *args, **kwargs):
        return FakeProcessContext()


class ConsumerStub(BaseConsumer):
    """Потребитель с заглушкой обработки сообщения."""

    async def process_message(self, body, raw_message, message_id=None):
        pass


class CustomDecoderConsumer(ConsumerStub):
    """Потребитель с переопределённым декодированием сообщения."""

    def decode_message(self, message):
        return {'custom': True}


class BodyLoggingDisabledConsumer(ConsumerStub):
    """Потребитель с отключённым логированием тела сообщения."""

    log_message_body = False


def create_consumer(consumer_class=ConsumerStub):
    """Создание потребителя без подключения к RabbitMQ."""
    return consumer_class('amqp://guest:guest@localhost:5672/', loop=asyncio.get_running_loop())


async def test_handle_delivery__logs_body_by_default(mocker, caplog):
    """По умолчанию тело сообщения логируется, как и раньше."""
    caplog.set_level(logging.DEBUG, logger='mq_misc.amqp')
    pformat_mock = mocker.patch('mq_misc.amqp.pprint.pformat', return_value='formatted body')
    consumer = create_consumer()
    consumer.process_message = mocker.AsyncMock()

    await consumer._handle_delivery(FakeIncomingMessage(b'{"success": true}'))

    pformat_mock.assert_called_once_with({'success': True})
    assert 'body: formatted body' in caplog.text


async def test_handle_delivery__logs_metadata_without_body(mocker, caplog):
    """Метаданные логируются, тело не форматируется при отключённом флаге."""
    caplog.set_level(logging.DEBUG, logger='mq_misc.amqp')
    pformat_mock = mocker.patch('mq_misc.amqp.pprint.pformat')
    consumer = create_consumer(BodyLoggingDisabledConsumer)
    consumer.process_message = mocker.AsyncMock()
    message = FakeIncomingMessage(b'{"success": true}', routing_key='Action.deploy.run.test', redelivered=True)

    await consumer._handle_delivery(message)

    consumer.process_message.assert_awaited_once()
    assert consumer.process_message.await_args.args[0] == {'success': True}
    pformat_mock.assert_not_called()
    assert 'routing_key: Action.deploy.run.test' in caplog.text
    assert 'body_size: 17' in caplog.text
    assert 'redelivered: True' in caplog.text
    assert 'body: {' not in caplog.text


async def test_handle_delivery__uses_decoder_override(mocker):
    """Потребитель может переопределить декодирование тела сообщения."""
    decode_mock = mocker.patch('mq_misc.amqp.decode_message')
    consumer = create_consumer(CustomDecoderConsumer)
    consumer.process_message = mocker.AsyncMock()

    await consumer._handle_delivery(FakeIncomingMessage(b'{"large": "body"}'))

    consumer.process_message.assert_awaited_once()
    assert consumer.process_message.await_args.args[0] == {'custom': True}
    decode_mock.assert_not_called()


async def test_handle_delivery__log_message_body_disabled_at_info(mocker, caplog):
    """При уровне INFO тело не форматируется, даже если флаг включён."""
    caplog.set_level(logging.INFO, logger='mq_misc.amqp')
    pformat_mock = mocker.patch('mq_misc.amqp.pprint.pformat')
    consumer = create_consumer()
    consumer.process_message = mocker.AsyncMock()

    await consumer._handle_delivery(FakeIncomingMessage(b'{"success": true}'))

    pformat_mock.assert_not_called()
