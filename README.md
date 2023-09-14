# Базовое API для работы с RabbitMQ

``BaseConsumer`` - базовый потребитель очереди сообщений  
``Publisher`` - базовый издатель очереди сообщений  
``ReplyToConsumer`` - reply to потребитель

## Python modules

### mq_misc.publish info

```
python -m mq_misc.publish  -h

usage: __main__.py [-h] [-m MESSAGE] [-f MESSAGE_FILE] -url AMQP_URL
                   [-q QUEUE] [-e EXCHANGE] [--exchange_type EXCHANGE_TYPE]
                   [-k ROUTING_KEY] [-to REPLY_TO] [-id CORRELATION_ID] [-w]

If an arg is specified in more than one place, then commandline values
override environment variables which override defaults.

optional arguments:
  -h, --help            show this help message and exit
  -m MESSAGE, --message MESSAGE
                        The message being sent [env var: RMQ_MESSAGE]
                        (default: None)
  -f MESSAGE_FILE, --message-file MESSAGE_FILE
                        File with the message [env var: RMQ_MESSAGE_FILE]
                        (default: None)
  -to REPLY_TO, --reply_to REPLY_TO
                        Commonly used to name a callback queue [env var:
                        RMQ_REPLY_TO] (default: None)
  -id CORRELATION_ID, --correlation_id CORRELATION_ID
                        Useful to correlate RPC responses with requests. [env
                        var: RMQ_CORRELATION_ID] (default: None)
  -w, --waiting_response
                        Waiting reply_to response. [env var:
                        RMQ_WAITING_RESPONSE] (default: False)

Rabbit MQ options:
  -url AMQP_URL, --amqp-url AMQP_URL
                        URL to use to connect to the rabbitmq [env var:
                        RMQ_AMQP_URL] (default: None)
  -q QUEUE, --queue QUEUE
                        Queue to use to connect to the rabbitmq [env var:
                        RMQ_QUEUE] (default: None)
  -e EXCHANGE, --exchange EXCHANGE
                        Exchange to use to connect to the rabbitmq [env var:
                        RMQ_EXCHANGE] (default: None)
  --exchange_type EXCHANGE_TYPE
                        Exchange type to use to connect to the rabbitmq [env
                        var: RMQ_EXCHANGE_TYPE] (default: direct)
  -k ROUTING_KEY, --routing_key ROUTING_KEY
                        Routing key for publish message [env var:
                        RMQ_ROUTING_KEY] (default: None)


```

python -m mq_misc.publish --amqp-url "amqp://guest:guest@localhost:5672/" --exchange "exchange_1" --exchange_type "
topic" --routing_key "log.error" --message-file "message.json"