import asyncio
import sys

import pytest

from mq_misc.consume.__main__ import _run as consume_run
from mq_misc.consume.__main__ import async_main as consume_async_main
from mq_misc.consume.__main__ import main as consume_main
from mq_misc.consume.__main__ import parser as consume_parser
from mq_misc.publish.__main__ import main as publish_main

URL = 'amqp://guest:guest@localhost:5672/'


def test_publish_main__runs_async_main(mocker):
    """main публикует сообщение через asyncio.run и вызывает async_main."""
    mocker.patch.object(sys, 'argv', ['mq_misc.publish', '-url', URL, '-m', '{}'])
    async_main_mock = mocker.patch('mq_misc.publish.__main__.async_main', new_callable=mocker.AsyncMock)

    publish_main()

    async_main_mock.assert_awaited_once()


def test_publish_main__propagates_error(mocker):
    """Ошибка публикации не глотается и приводит к ненулевому exit code."""
    mocker.patch.object(sys, 'argv', ['mq_misc.publish', '-url', URL, '-m', '{}'])
    mocker.patch(
        'mq_misc.publish.__main__.async_main',
        new_callable=mocker.AsyncMock,
        side_effect=RuntimeError('publish failed'),
    )

    with pytest.raises(RuntimeError, match='publish failed'):
        publish_main()


async def test_run__closes_consumer(mocker):
    """После остановки consumer закрывается, async_main получает аргументы."""
    consumer = mocker.Mock()
    consumer.close = mocker.AsyncMock()
    args = mocker.Mock()
    async_main_mock = mocker.patch('mq_misc.consume.__main__.async_main', new_callable=mocker.AsyncMock)
    stop_event = asyncio.Event()
    stop_event.set()

    await consume_run(consumer, args, stop_event)

    async_main_mock.assert_awaited_once_with(consumer, args)
    consumer.close.assert_awaited_once()


async def test_run__closes_consumer_on_error(mocker):
    """При ошибке подключения consumer закрывается, исключение пробрасывается."""
    consumer = mocker.Mock()
    consumer.close = mocker.AsyncMock()
    mocker.patch(
        'mq_misc.consume.__main__.async_main',
        new_callable=mocker.AsyncMock,
        side_effect=RuntimeError('connect failed'),
    )

    with pytest.raises(RuntimeError, match='connect failed'):
        await consume_run(consumer, mocker.Mock(), asyncio.Event())

    consumer.close.assert_awaited_once()


def test_consume_main__handles_keyboard_interrupt(mocker):
    """Ctrl+C завершает CLI без повторного запуска loop и без ошибки."""
    mocker.patch.object(sys, 'argv', ['mq_misc.consume', '-url', URL])
    mocker.patch('mq_misc.consume.__main__.DebugConsumer')

    def raise_keyboard_interrupt(coro):
        coro.close()
        raise KeyboardInterrupt

    mocker.patch('mq_misc.consume.__main__.asyncio.run', side_effect=raise_keyboard_interrupt)

    consume_main()


async def test_consume_async_main__durable_by_default(mocker):
    """По умолчанию consumer объявляет durable-очередь."""
    consumer = mocker.Mock()
    consumer.create_consume_connection = mocker.AsyncMock()
    args = consume_parser.parse_args(['-url', URL])

    await consume_async_main(consumer, args)

    assert consumer.create_consume_connection.await_args.kwargs['durable'] is True


async def test_consume_async_main__durable_can_be_disabled(mocker):
    """Явный --durable false переопределяет durable-дефолт."""
    consumer = mocker.Mock()
    consumer.create_consume_connection = mocker.AsyncMock()
    args = consume_parser.parse_args(['-url', URL, '--durable', 'false'])

    await consume_async_main(consumer, args)

    assert consumer.create_consume_connection.await_args.kwargs['durable'] is False
