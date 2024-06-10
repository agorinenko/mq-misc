# RabbitMQ Utils

## The basic API for working with RabbitMQ

``BaseConsumer`` - the basic consumer of the message queue  
``Publisher`` - the basic publisher of the message queue
``ReplyToConsumer`` - reply to consumer

## MQ commands

### Publish message

Publishing a message to the queue

```
python -m mq_misc.publish [-h] [-m MESSAGE] [-f MESSAGE_FILE] -url AMQP_URL
                   [-q QUEUE] [-e EXCHANGE] [--exchange_type EXCHANGE_TYPE]
                   [-k ROUTING_KEY] [-to REPLY_TO] [-id CORRELATION_ID] [-w]

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

For example

```
python -m mq_misc.publish -u "amqp://guest:guest@localhost:5672/" -e "exchange_1" --exchange_type "topic" --routing_key "log.error" -f "message.json" -w
python -m mq_misc.publish -u "amqp://guest:guest@localhost:5672/" -q "queue_1" -f "message.json" -w
```

## Consume message

Consuming a message from the queue

```
usage: python -m mq_misc.consume [-h] -url AMQP_URL [-q QUEUE] [-e EXCHANGE]
                   [--exchange_type EXCHANGE_TYPE] [--ssl SSL]
                   [--durable DURABLE] [--robust ROBUST]
                   [--declare_exchange DECLARE_EXCHANGE] [-b BINDING_KEYS]
                   [-pc PREFETCH_COUNT]

If an arg is specified in more than one place, then commandline values
override environment variables which override defaults.

optional arguments:
  -h, --help            show this help message and exit

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
  --ssl SSL             Use SSL for connection. [env var: RMQ_SSL] (default:
                        false)
  --durable DURABLE     Use durable connection. [env var: RMQ_DURABLE]
                        (default: false)
  --robust ROBUST       Make robust connection to the broker. [env var:
                        RMQ_ROBUST] (default: false)
  --declare_exchange DECLARE_EXCHANGE
                        Declare an exchange. [env var: RMQ_DECLARE_EXCHANGE]
                        (default: false)
  -b BINDING_KEYS, --binding_keys BINDING_KEYS
                        Binding keys separated by commas. [env var:
                        RMQ_BINDING_KEYS] (default: None)
  -pc PREFETCH_COUNT, --prefetch_count PREFETCH_COUNT
                        Consumer prefetch [env var: RMQ_PREFETCH_COUNT]
                        (default: 10)
```

For example

```
python -m mq_misc.consume -u "amqp://guest:guest@localhost:5672/" -q "queue_1" -e "exchange_1" --exchange_type "topic" -b "log.level.*"  --durable "true" --robust "true" --declare_exchange "true"
```

## Creating release tags

```
git tag -a 0.0.6 -m "Release 0.0.6"
```