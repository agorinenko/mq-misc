# mq-misc

Утилиты для работы с RabbitMQ на базе [aio-pika](https://aio-pika.readthedocs.io/):
базовые адаптеры, потребитель, издатель, reply-to потребитель и CLI для публикации
и чтения сообщений.

## Требования

- Python 3.10+
- aio_pika 9.6+

Пакет проверяется в CI на Python 3.10–3.14.

## Установка

```bash
pip install mq-misc
```

Для разработки:

```bash
pip install -e ".[test]"
```

## Быстрый старт

### Публикация сообщения

`create_weak_publisher` создаёт краткоживущее подключение и закрывает его
при выходе из контекста:

```python
import asyncio

from mq_misc.amqp import create_weak_publisher

URL = 'amqp://guest:guest@localhost:5672/'


async def main():
    async with create_weak_publisher(URL, 'queue_1') as publisher:
        await publisher.publish({'message': 'hello'})


asyncio.run(main())
```

Если нужен долгоживущий издатель:

```python
import asyncio

from mq_misc.amqp import Publisher

URL = 'amqp://guest:guest@localhost:5672/'


async def main():
    publisher = Publisher(URL, queue_name='queue_1')
    await publisher.create_connection(robust=False)
    try:
        await publisher.publish({'message': 'hello'})
    finally:
        await publisher.close()


asyncio.run(main())
```

`Publisher.publish` принимает `str` или `dict`. Для `str` тело сначала
разбирается как JSON и затем сериализуется заново. Дополнительные аргументы
передаются в `aio_pika.Message` (`delivery_mode`, `reply_to`, `correlation_id`
и т.п.), `routing_key` по умолчанию равен `queue_name`.

### Получение сообщений

```python
import asyncio

from mq_misc.amqp import BaseConsumer

URL = 'amqp://guest:guest@localhost:5672/'


class MyConsumer(BaseConsumer):
    async def process_message(self, body, raw_message, message_id=None):
        print(message_id, body)


async def main():
    consumer = MyConsumer(URL, 'queue_1')
    await consumer.create_consume_connection(robust=False)
    try:
        await asyncio.Event().wait()
    finally:
        await consumer.close()


asyncio.run(main())
```

`BaseConsumer`:

- `process_message(body, raw_message, message_id=None)` — обязательный метод,
  вызывается после декодирования сообщения;
- `decode_message(message)` — декодирование тела; по умолчанию `json.loads`.
  Наследник может переопределить метод, чтобы извлекать только нужные поля,
  не материализуя всё тело (например, потоковым JSON-парсером);
- `log_message_body` — флаг логирования тела на уровне `DEBUG`, по умолчанию
  `True`. Для больших сообщений `pprint.pformat` может быть дорогим, поэтому
  в наследнике можно указать `log_message_body = False`;
- `publish_response(incoming_message, message)` — публикация ответа в
  `reply_to` с `correlation_id` входящего сообщения.

`create_consume_connection` по умолчанию создаёт robust-подключение и принимает
`prefetch_count`, `ssl`, `ssl_options`, `ssl_context`, `declare_exchange`,
`exchange_kwargs`, а также параметры объявления очереди (`durable`, `exclusive`,
`auto_delete`, `binding_keys`, `no_ack`).

### Reply-to потребитель

`ReplyToConsumer` публикует сообщение и ждёт ответ в собственной эксклюзивной
очереди. Время ожидания задаётся свойством `timeout` (по умолчанию ждёт
бесконечно):

```python
from mq_misc.amqp import ReplyToConsumer, create_weak_publisher

URL = 'amqp://guest:guest@localhost:5672/'


class RequestConsumer(ReplyToConsumer):
    @property
    def timeout(self):
        return 5

    async def process_message(self, body, raw_message, message_id=None):
        pass


async def main():
    async with create_weak_publisher(URL, 'service_queue') as publisher:
        consumer = RequestConsumer(URL)
        await consumer.create_consume_connection(robust=False)
        try:
            result = await consumer.publish({'request': True}, publisher)
            print(result)
        finally:
            await consumer.close()
```

### Декодирование сообщений

```python
class TriggerConsumer(BaseConsumer):
    def decode_message(self, message):
        return extract_trigger_fields(message.body)
```

Модульная функция `mq_misc.amqp.decode_message` используется по умолчанию.

### SSL

Параметры `ssl`, `ssl_options`, `ssl_context` передаются в `aio_pika.connect`:

```python
import asyncio
import ssl

from mq_misc.amqp import create_weak_publisher

URL = 'amqps://user:password@rabbitmq.example.com:5671/'
context = ssl.create_default_context(cafile='ca.pem')


async def main():
    async with create_weak_publisher(URL, 'queue_1', ssl_context=context) as publisher:
        await publisher.publish({'message': 'hello'})


asyncio.run(main())
```

Для URI со схемой `amqps://` TLS включается на стороне `aio-pika`/`aiormq`.

### Event loop

`BaseAdapter` (и его наследники) можно создавать вне корутины. Если `loop` не
передан, он резолвится лениво из текущего running loop при подключении или
первом обращении к свойству `loop`. Обращение к `adapter.loop` вне корутины без
явно переданного loop вызывает `RuntimeError`.

Устаревший синхронный хелпер `start_server(async_task, loop=None)` создаёт новый
event loop, если loop не передан, запускает `async_task(loop)` и вызывает
`run_forever()`. В новом коде используйте `asyncio.run`.

## Команды MQ

Переменные окружения используют префикс `RMQ_`; значения из командной строки
переопределяют переменные окружения, а те — значения по умолчанию.

### Публикация сообщения

```bash
python -m mq_misc.publish --help
```

```text
usage: python -m mq_misc.publish [-h] [-m MESSAGE] [-f MESSAGE_FILE]
                                 -url AMQP_URL [-q QUEUE] [-e EXCHANGE]
                                 [--exchange_type EXCHANGE_TYPE]
                                 [-k ROUTING_KEY] [-to REPLY_TO]
                                 [-id CORRELATION_ID] [-w]

options:
  -h, --help            show this help message and exit
  -m, --message MESSAGE
                        The message being sent [env var: RMQ_MESSAGE]
                        (default: None)
  -f, --message-file MESSAGE_FILE
                        File with the message [env var: RMQ_MESSAGE_FILE]
                        (default: None)
  -to, --reply_to REPLY_TO
                        Commonly used to name a callback queue [env var:
                        RMQ_REPLY_TO] (default: None)
  -id, --correlation_id CORRELATION_ID
                        Useful to correlate RPC responses with requests. [env
                        var: RMQ_CORRELATION_ID] (default: None)
  -w, --waiting_response
                        Waiting reply_to response. [env var:
                        RMQ_WAITING_RESPONSE] (default: False)

Rabbit MQ options:
  -url, --amqp-url AMQP_URL
                        URL to use to connect to the rabbitmq [env var:
                        RMQ_AMQP_URL]
  -q, --queue QUEUE     Queue to use to connect to the rabbitmq [env var:
                        RMQ_QUEUE] (default: None)
  -e, --exchange EXCHANGE
                        Exchange to use to connect to the rabbitmq [env var:
                        RMQ_EXCHANGE] (default: None)
  --exchange_type EXCHANGE_TYPE
                        Exchange type to use to connect to the rabbitmq [env
                        var: RMQ_EXCHANGE_TYPE] (default: direct)
  -k, --routing_key ROUTING_KEY
                        Routing key for publish message [env var:
                        RMQ_ROUTING_KEY] (default: None)

 In general, command-line values override environment variables which override
defaults.
```

Обязателен только `-url/--amqp-url`; дополнительно нужно передать сообщение
через `-m/--message` или файл через `-f/--message-file`. Параметр `-w` ждёт
ответ в `reply_to` около 3 секунд и печатает его в лог.

Примеры:

```bash
python -m mq_misc.publish --amqp-url "amqp://guest:guest@localhost:5672/" \
    -q "queue_1" -f "message.json"

python -m mq_misc.publish --amqp-url "amqp://guest:guest@localhost:5672/" \
    -e "exchange_1" --exchange_type "topic" --routing_key "log.error" \
    -f "message.json"

python -m mq_misc.publish --amqp-url "amqp://guest:guest@localhost:5672/" \
    -q "queue_1" -m '{"message": "hello"}' -w
```

Обратите внимание: длинные опции `--exchange_type`, `--routing_key`,
`--reply_to`, `--correlation_id` записываются через подчёркивание, а `-url` —
это отдельная опция из одного дефиса. Сокращения вида `-u` и `--exchange-type`
не поддерживаются.

### Получение сообщений

```bash
python -m mq_misc.consume --help
```

```text
usage: python -m mq_misc.consume [-h] -url AMQP_URL [-q QUEUE] [-e EXCHANGE]
                                 [--exchange_type EXCHANGE_TYPE] [--ssl SSL]
                                 [--durable DURABLE] [--robust ROBUST]
                                 [--declare_exchange DECLARE_EXCHANGE]
                                 [-b BINDING_KEYS] [-pc PREFETCH_COUNT]

options:
  -h, --help            show this help message and exit

Rabbit MQ options:
  -url, --amqp-url AMQP_URL
                        URL to use to connect to the rabbitmq [env var:
                        RMQ_AMQP_URL]
  -q, --queue QUEUE     Queue to use to connect to the rabbitmq [env var:
                        RMQ_QUEUE] (default: None)
  -e, --exchange EXCHANGE
                        Exchange to use to connect to the rabbitmq [env var:
                        RMQ_EXCHANGE] (default: None)
  --exchange_type EXCHANGE_TYPE
                        Exchange type to use to connect to the rabbitmq [env
                        var: RMQ_EXCHANGE_TYPE] (default: direct)
  --ssl SSL             Use SSL for connection. [env var: RMQ_SSL] (default:
                        false)
  --durable DURABLE     Use durable connection. [env var: RMQ_DURABLE]
                        (default: false)
  --robust ROBUST       Make robust connection to the broker. [env var:
                        RMQ_ROBUST] (default: false)
  --declare_exchange DECLARE_EXCHANGE
                        Declare an exchange. [env var: RMQ_DECLARE_EXCHANGE]
                        (default: false)
  -b, --binding_keys BINDING_KEYS
                        Binding keys separated by commas. [env var:
                        RMQ_BINDING_KEYS] (default: None)
  -pc, --prefetch_count PREFETCH_COUNT
                        Consumer prefetch [env var: RMQ_PREFETCH_COUNT]
                        (default: 10)

 In general, command-line values override environment variables which override
defaults.
```

`--ssl`, `--durable`, `--robust`, `--declare_exchange` принимают значение:
`yes`, `true`, `t`, `1`, `no`, `false`, `f`, `0`.

Пример:

```bash
python -m mq_misc.consume --amqp-url "amqp://guest:guest@localhost:5672/" \
    -q "queue_1" -e "exchange_1" --exchange_type "topic" \
    -b "log.level.*" --durable true --robust true --declare_exchange true
```

## Тесты

```bash
pip install -e ".[test]"
python -m pytest
```

Интеграционные тесты требуют RabbitMQ. Адрес по умолчанию —
`amqp://guest:guest@localhost:5672/`, переопределяется переменной
`MQ_MISC_TEST_AMQP_URL`:

```bash
MQ_MISC_TEST_AMQP_URL="amqp://user:password@rabbitmq:5672/" python -m pytest
```

CI-матрица: Python 3.10–3.14 с RabbitMQ, плюс отдельная проверка на
aio-pika 9.6.2.

## Релиз

```bash
git tag -a 0.1.0 -m "Release 0.1.0"
python -m pip install --upgrade build twine
python -m build
python -m twine upload dist/*
```
