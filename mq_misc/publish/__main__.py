import argparse
import asyncio
import logging
from typing import Optional

from configargparse import ArgumentParser

from mq_misc.amqp import Publisher

parser = ArgumentParser(
    auto_env_var_prefix="RMQ_", allow_abbrev=False,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("--message", required=False, help='The message being sent')
parser.add_argument("--message-file", required=False, help='File with the message')

group = parser.add_argument_group('Rabbit MQ options')
group.add_argument('--amqp-url', required=True, help='URL to use to connect to the rabbitmq')
group.add_argument('--queue', required=False, help='Queue to use to connect to the rabbitmq')
group.add_argument('--exchange', required=False, help='Exchange to use to connect to the rabbitmq')
group.add_argument('--exchange_type', required=False, help='Exchange type to use to connect to the rabbitmq', default='direct')
group.add_argument('--routing_key', required=False, help='Routing key for publish message')

logger = logging.getLogger("PUBLISH MESSAGE")


async def async_main(publisher: Publisher, message: str, routing_key: Optional[str]):
    logger.info("Connecting...")
    await publisher.create_connection(robust=False)

    if publisher.exchange_name:
        await publisher.declare_exchange(durable=True)

    logger.info("Publish message...")

    params = {}
    if routing_key:
        params['routing_key'] = routing_key

    await publisher.publish(message, **params)
    logger.info("OK...")


def main():
    logging.basicConfig(level=logging.INFO)

    args = parser.parse_args()

    loop = asyncio.get_event_loop()

    url = args.amqp_url
    queue = args.queue
    exchange = args.exchange
    exchange_type = args.exchange_type
    message = args.message
    routing_key = args.routing_key

    if message is None:
        message_file = args.message_file
        with open(message_file, 'r') as f:
            message = f.read()

    publisher = Publisher(url, queue, exchange_name=exchange, exchange_type=exchange_type, loop=loop)



    try:
        loop.run_until_complete(async_main(publisher, message, routing_key=routing_key))
    finally:
        loop.run_until_complete(publisher.close())


if __name__ == '__main__':
    main()
