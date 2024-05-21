import argparse
import asyncio
import logging
import pprint
import uuid
from typing import Optional

import aio_pika
from aio_pika import DeliveryMode
from configargparse import ArgumentParser

from mq_misc.amqp import create_weak_publisher, ReplyToConsumer

parser = ArgumentParser(
    auto_env_var_prefix="RMQ_", allow_abbrev=False,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument('-m', '--message', required=False, help='The message being sent')
parser.add_argument('-f', '--message-file', required=False, help='File with the message')

group = parser.add_argument_group('Rabbit MQ options')
group.add_argument('-url', '--amqp-url', required=True, help='URL to use to connect to the rabbitmq')
group.add_argument('-q', '--queue', required=False, help='Queue to use to connect to the rabbitmq')
group.add_argument('-e', '--exchange', required=False, help='Exchange to use to connect to the rabbitmq')
group.add_argument('--exchange_type', required=False, help='Exchange type to use to connect to the rabbitmq',
                   default='direct')
group.add_argument('-k', '--routing_key', required=False, help='Routing key for publish message')
parser.add_argument('-to', '--reply_to', help='Commonly used to name a callback queue', required=False)
parser.add_argument('-id', '--correlation_id', help='Useful to correlate RPC responses with requests.', required=False)
parser.add_argument('-w', '--waiting_response', action='store_true', help='Waiting reply_to response.')

logger = logging.getLogger('PUBLISH MESSAGE')


class SimpleReplyToConsumer(ReplyToConsumer):
    async def process_message(self, body: dict, raw_message: aio_pika.IncomingMessage, **kwargs) -> None:
        logger.info('Response...\n%s', pprint.pformat(body))


async def async_main(args):
    try:
        url = args.amqp_url
        queue = args.queue
        exchange = args.exchange
        exchange_type = args.exchange_type
        message = args.message
        routing_key = args.routing_key
        reply_to = args.reply_to
        correlation_id = args.correlation_id
        waiting_response = args.waiting_response

        if not message:
            message_file = args.message_file
            if not message_file:
                raise ValueError('Specify message or file')

            with open(message_file, 'r') as f:
                message = f.read()

        logger.info('Connecting...')
        async with create_weak_publisher(url, queue, exchange_name=exchange, exchange_type=exchange_type) as publisher:
            if publisher.exchange_name:
                await publisher.declare_exchange(durable=True)

            logger.info('Publish message...')

            params = {
                'delivery_mode': DeliveryMode.NOT_PERSISTENT
            }
            if routing_key:
                params['routing_key'] = routing_key

            if reply_to:
                params['reply_to'] = reply_to

            if correlation_id:
                params['correlation_id'] = correlation_id

            if waiting_response:
                request_consumer = SimpleReplyToConsumer(url)

                await request_consumer.create_consume_connection(robust=False)
                try:
                    await request_consumer.publish(message, publisher)
                    await asyncio.sleep(3)
                finally:
                    await request_consumer.close()

            else:
                await publisher.publish(message, **params)

        logger.info('OK...')
    except Exception as ex:
        logger.exception(ex)


def main():
    logging.basicConfig(level=logging.INFO)

    args = parser.parse_args()

    loop = asyncio.get_event_loop()

    loop.run_until_complete(async_main(args))


if __name__ == '__main__':
    main()
