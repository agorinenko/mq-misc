# Базовое API для работы с RabbitMQ
``BaseConsumer`` - базовый потребитель очереди сообщений  
``Publisher`` - базовый издатель очереди сообщений  
``ReplyToConsumer`` -  reply to потребитель  
## Python modules
### mq_misc.publish
```
python -m mq_misc.publish  -h

usage: __main__.py [-h] [--message MESSAGE] [--message-file MESSAGE_FILE] --amqp-url AMQP_URL --amqp-queue AMQP_QUEUE

If an arg is specified in more than one place, then commandline values override environment variables which override defaults.

optional arguments:
  -h, --help            show this help message and exit
  --message MESSAGE     The message being sent [env var: RMQ_MESSAGE] (default: None)
  --message-file MESSAGE_FILE
                        File with the message [env var: RMQ_MESSAGE_FILE] (default: None)

Rabbit MQ options:
  --amqp-url AMQP_URL   URL to use to connect to the rabbitmq [env var: RMQ_AMQP_URL] (default: None)
  --amqp-queue AMQP_QUEUE
                        Queue to use to connect to the rabbitmq [env var: RMQ_AMQP_QUEUE] (default: None)
```
