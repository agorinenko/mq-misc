import argparse
import asyncio
import logging
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
group.add_argument('--amqp-queue', required=True, help='Queue to use to connect to the rabbitmq')

logger = logging.getLogger("PUBLISH MESSAGE")


async def async_main(publisher: Publisher, message: str):
    logger.info("Connecting...")
    await publisher.create_connection(robust=False)
    logger.info("Publish message...")
    await publisher.publish(message)
    logger.info("OK...")


def main():
    logging.basicConfig(level=logging.INFO)

    args = parser.parse_args()

    loop = asyncio.get_event_loop()

    url = args.amqp_url
    queue = args.amqp_queue
    message = args.message

    if message is None:
        message_file = args.message_file
        with open(message_file, 'r') as f:
            message = f.read()

    publisher = Publisher(url, queue, loop=loop)

    try:
        loop.run_until_complete(async_main(publisher, message))
    finally:
        loop.run_until_complete(publisher.close())


if __name__ == '__main__':
    main()
