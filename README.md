# Базовое API для работы с RabbitMQ

``BaseConsumer`` - базовый потребитель очереди сообщений  
``Publisher`` - базовый издатель очереди сообщений  
``ReplyToConsumer`` - reply to потребитель

## Python modules

### mq_misc.publish

```
python -m mq_misc.publish  -h

usage: __main__.py [-h] [--message MESSAGE] [--message-file MESSAGE_FILE] --amqp-url AMQP_URL --queue QUEUE [--exchange EXCHANGE] [--exchange_type EXCHANGE_TYPE] [--routing_key ROUTING_KEY]

If an arg is specified in more than one place, then commandline values override environment variables which override defaults.

optional arguments:
  -h, --help            show this help message and exit
  --message MESSAGE     The message being sent [env var: RMQ_MESSAGE] (default: None)
  --message-file MESSAGE_FILE
                        File with the message [env var: RMQ_MESSAGE_FILE] (default: None)

Rabbit MQ options:
  --amqp-url AMQP_URL   URL to use to connect to the rabbitmq [env var: RMQ_AMQP_URL] (default: None)
  --queue QUEUE         Queue to use to connect to the rabbitmq [env var: RMQ_QUEUE] (default: None)
  --exchange EXCHANGE   Exchange to use to connect to the rabbitmq [env var: RMQ_EXCHANGE] (default: None)
  --exchange_type EXCHANGE_TYPE
                        Exchange type to use to connect to the rabbitmq [env var: RMQ_EXCHANGE_TYPE] (default: direct)
  --routing_key ROUTING_KEY
                        Routing key for publish message [env var: RMQ_ROUTING_KEY] (default: None)

```
python -m mq_misc.publish  --amqp-url "amqp://guest:guest@localhost:5672/" --exchange "exchange_1" --exchange_type "topic" --routing_key "log.error" --message-file "message.json"