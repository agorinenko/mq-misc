from mq_misc.amqp import Publisher

URL = 'amqp://guest:guest@localhost:5672/'


def create_publisher_with_mock_channel(mocker):
    """Publisher с замоканным каналом для проверки declare_queue."""
    publisher = Publisher(URL)
    channel = mocker.Mock()
    channel.declare_queue = mocker.AsyncMock(return_value=mocker.Mock())
    publisher.channel = channel
    return publisher


async def test_declare_queue__durable_by_default(mocker):
    """По умолчанию очередь объявляется durable."""
    publisher = create_publisher_with_mock_channel(mocker)

    await publisher.declare_queue()

    assert publisher.channel.declare_queue.await_args.kwargs['durable'] is True


async def test_declare_queue__honors_explicit_durable_false(mocker):
    """Явное durable=False переопределяет значение по умолчанию."""
    publisher = create_publisher_with_mock_channel(mocker)

    await publisher.declare_queue(durable=False)

    assert publisher.channel.declare_queue.await_args.kwargs['durable'] is False
