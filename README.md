# Утилиты RabbitMQ

## Базовое API для работы с RabbitMQ

``BaseConsumer`` — базовый потребитель очереди сообщений  
``Publisher`` — базовый издатель сообщений в очередь  
``ReplyToConsumer`` — потребитель с ответом (reply-to)

### Декодирование сообщений потребителем

По умолчанию ``BaseConsumer`` декодирует всё тело сообщения через ``json.loads``.
Потребитель может переопределить ``decode_message``, чтобы извлекать только нужные поля,
не материализуя всё тело (например, с помощью потокового JSON-парсера):

```python
class TriggerConsumer(BaseConsumer):
    def decode_message(self, message):
        return extract_trigger_fields(message.body)
```

Тело сообщения по умолчанию логируется (прежнее поведение). Для больших сообщений
``pprint.pformat`` может потреблять много памяти и CPU, поэтому логирование можно
отключить в потребителе:

```python
class QuietConsumer(BaseConsumer):
    log_message_body = False
```

## Команды MQ

### Публикация сообщения

Публикация сообщения в очередь

```
использование: python -m mq_misc.publish [-h] [-m MESSAGE] [-f MESSAGE_FILE] -url AMQP_URL
                   [-q QUEUE] [-e EXCHANGE] [--exchange_type EXCHANGE_TYPE]
                   [-k ROUTING_KEY] [-to REPLY_TO] [-id CORRELATION_ID] [-w]

необязательные аргументы:
  -h, --help            показать это сообщение и выйти
  -m MESSAGE, --message MESSAGE
                        Отправляемое сообщение [переменная окружения: RMQ_MESSAGE]
                        (по умолчанию: None)
  -f MESSAGE_FILE, --message-file MESSAGE_FILE
                        Файл с сообщением [переменная окружения: RMQ_MESSAGE_FILE]
                        (по умолчанию: None)
  -to REPLY_TO, --reply_to REPLY_TO
                        Обычно используется для имени очереди ответа [переменная
                        окружения: RMQ_REPLY_TO] (по умолчанию: None)
  -id CORRELATION_ID, --correlation_id CORRELATION_ID
                        Полезно для сопоставления RPC-ответов с запросами.
                        [переменная окружения: RMQ_CORRELATION_ID]
                        (по умолчанию: None)
  -w, --waiting_response
                        Ожидать ответ в reply_to. [переменная окружения:
                        RMQ_WAITING_RESPONSE] (по умолчанию: False)

Параметры RabbitMQ:
  -url AMQP_URL, --amqp-url AMQP_URL
                        URL для подключения к RabbitMQ [переменная окружения:
                        RMQ_AMQP_URL] (по умолчанию: None)
  -q QUEUE, --queue QUEUE
                        Очередь для подключения к RabbitMQ [переменная окружения:
                        RMQ_QUEUE] (по умолчанию: None)
  -e EXCHANGE, --exchange EXCHANGE
                        Exchange для подключения к RabbitMQ [переменная окружения:
                        RMQ_EXCHANGE] (по умолчанию: None)
  --exchange_type EXCHANGE_TYPE
                        Тип exchange для подключения к RabbitMQ [переменная
                        окружения: RMQ_EXCHANGE_TYPE] (по умолчанию: direct)
  -k ROUTING_KEY, --routing_key ROUTING_KEY
                        Routing key для публикуемого сообщения [переменная
                        окружения: RMQ_ROUTING_KEY] (по умолчанию: None)


```

Пример

```
python -m mq_misc.publish -u "amqp://guest:guest@localhost:5672/" -e "exchange_1" --exchange_type "topic" --routing_key "log.error" -f "message.json" -w
python -m mq_misc.publish -u "amqp://guest:guest@localhost:5672/" -q "queue_1" -f "message.json" -w
```

## Получение сообщений

Получение сообщения из очереди

```
использование: python -m mq_misc.consume [-h] -url AMQP_URL [-q QUEUE] [-e EXCHANGE]
                   [--exchange_type EXCHANGE_TYPE] [--ssl SSL]
                   [--durable DURABLE] [--robust ROBUST]
                   [--declare_exchange DECLARE_EXCHANGE] [-b BINDING_KEYS]
                   [-pc PREFETCH_COUNT]

Если аргумент указан в нескольких местах, значения из командной строки
переопределяют переменные окружения, которые переопределяют значения по умолчанию.

необязательные аргументы:
  -h, --help            показать это сообщение и выйти

Параметры RabbitMQ:
  -url AMQP_URL, --amqp-url AMQP_URL
                        URL для подключения к RabbitMQ [переменная окружения:
                        RMQ_AMQP_URL] (по умолчанию: None)
  -q QUEUE, --queue QUEUE
                        Очередь для подключения к RabbitMQ [переменная окружения:
                        RMQ_QUEUE] (по умолчанию: None)
  -e EXCHANGE, --exchange EXCHANGE
                        Exchange для подключения к RabbitMQ [переменная окружения:
                        RMQ_EXCHANGE] (по умолчанию: None)
  --exchange_type EXCHANGE_TYPE
                        Тип exchange для подключения к RabbitMQ [переменная
                        окружения: RMQ_EXCHANGE_TYPE] (по умолчанию: direct)
  --ssl SSL             Использовать SSL для подключения. [переменная окружения:
                        RMQ_SSL] (по умолчанию: false)
  --durable DURABLE     Использовать durable-соединение. [переменная окружения:
                        RMQ_DURABLE] (по умолчанию: false)
  --robust ROBUST       Создать robust-соединение с брокером. [переменная
                        окружения: RMQ_ROBUST] (по умолчанию: false)
  --declare_exchange DECLARE_EXCHANGE
                        Объявить exchange. [переменная окружения:
                        RMQ_DECLARE_EXCHANGE] (по умолчанию: false)
  -b BINDING_KEYS, --binding_keys BINDING_KEYS
                        Binding keys через запятую. [переменная окружения:
                        RMQ_BINDING_KEYS] (по умолчанию: None)
  -pc PREFETCH_COUNT, --prefetch_count PREFETCH_COUNT
                        Prefetch потребителя [переменная окружения:
                        RMQ_PREFETCH_COUNT] (по умолчанию: 10)
```

Пример

```
python -m mq_misc.consume -u "amqp://guest:guest@localhost:5672/" -q "queue_1" -e "exchange_1" --exchange_type "topic" -b "log.level.*"  --durable "true" --robust "true" --declare_exchange "true"
```

## Создание тегов релиза

```
git tag -a 0.0.6 -m "Release 0.0.6"
```
