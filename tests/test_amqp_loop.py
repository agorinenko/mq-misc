import asyncio

import pytest

from mq_misc.amqp import Publisher, start_server

URL = 'amqp://guest:guest@localhost:5672/'


def create_mock_connection(mocker):
    """Создание заглушки соединения aio_pika с каналом."""
    connection = mocker.Mock()
    channel = mocker.Mock()
    channel.default_exchange = mocker.Mock()
    channel.set_qos = mocker.AsyncMock()
    connection.channel = mocker.AsyncMock(return_value=channel)
    return connection


def test_publisher__constructs_outside_running_loop():
    """Адаптер создаётся вне корутины, loop резолвится позже."""
    publisher = Publisher(URL)

    assert publisher._loop is None
    with pytest.raises(RuntimeError):
        publisher.loop


async def test_publisher__resolves_running_loop():
    """Внутри корутины свойство loop возвращает текущий running loop."""
    publisher = Publisher(URL)

    assert publisher.loop is asyncio.get_running_loop()


def test_publisher__supports_loop_assignment():
    """Присваивание loop сохраняет обратную совместимость."""
    publisher = Publisher(URL)
    loop = object()

    publisher.loop = loop

    assert publisher.loop is loop


async def test_create_connection__passes_running_loop(mocker):
    """При подключении в aio_pika передаётся текущий running loop."""
    connection = create_mock_connection(mocker)
    connect_mock = mocker.patch('mq_misc.amqp.aio_pika.connect', new_callable=mocker.AsyncMock)
    connect_mock.return_value = connection
    publisher = Publisher(URL)

    await publisher.create_connection(robust=False)

    assert connect_mock.await_args.kwargs['loop'] is asyncio.get_running_loop()


def test_start_server__uses_explicit_loop(mocker):
    """start_server использует переданный loop и не создаёт новый."""
    loop = mocker.Mock()
    async_task = mocker.Mock(return_value=mocker.Mock())

    start_server(async_task, loop)

    loop.create_task.assert_called_once()
    loop.run_forever.assert_called_once()


def test_start_server__creates_loop_when_none(mocker):
    """Без переданного loop start_server создаёт и устанавливает новый."""
    loop = mocker.Mock()
    new_loop_mock = mocker.patch('mq_misc.amqp.asyncio.new_event_loop', return_value=loop)
    set_loop_mock = mocker.patch('mq_misc.amqp.asyncio.set_event_loop')
    async_task = mocker.Mock(return_value=mocker.Mock())

    start_server(async_task)

    new_loop_mock.assert_called_once()
    set_loop_mock.assert_called_once_with(loop)
    loop.create_task.assert_called_once()
    loop.run_forever.assert_called_once()
