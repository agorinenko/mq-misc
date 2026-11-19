import argparse
import asyncio
import logging
import uuid
from typing import Optional, Tuple

import aio_pika
from configargparse import ArgumentParser

from mq_misc.amqp import BaseConsumer

parser = ArgumentParser(
    auto_env_var_prefix="RMQ_", allow_abbrev=False,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

group = parser.add_argument_group('Rabbit MQ options')
group.add_argument('-url', '--amqp-url', required=True, help='URL to use to connect to the rabbitmq')
group.add_argument('-q', '--queue', required=False, help='Queue to use to connect to the rabbitmq')
group.add_argument('-e', '--exchange', required=False, help='Exchange to use to connect to the rabbitmq')
group.add_argument('--exchange_type', required=False, help='Exchange type to use to connect to the rabbitmq',
                   default='direct')

group.add_argument('--ssl', required=False, default='false', help='Use SSL for connection.')
group.add_argument('--durable', required=False, default='true', help='Declare a durable queue.')
group.add_argument('--robust', required=False, default='false', help='Make robust connection to the broker.')
group.add_argument('--declare_exchange', required=False, default='false', help='Declare an exchange.')
group.add_argument('-b', '--binding_keys', required=False, help='Binding keys separated by commas.')

group.add_argument('-pc', '--prefetch_count', required=False, default=10, help='Consumer prefetch', type=int)

logger = logging.getLogger('CONSUME MESSAGES')


class DebugConsumer(BaseConsumer):
    async def process_message(self, body: dict, raw_message: aio_pika.IncomingMessage,
                              message_id: Optional[uuid.UUID] = None) -> None:
        """ Запуск процесса прослушивания очереди и печати содержимого в лог """
        logger.debug('Hello, world!')


def _try_parse_bool(i: str) -> Tuple[bool, Optional[bool]]:
    try:
        i = str(i).lower()

        if i not in ('yes', 'true', 't', '1', 'no', 'false', 'f', '0'):
            raise ValueError()

        return True, i in ('yes', 'true', 't', '1')
    except ValueError:
        return False, None


async def async_main(consumer, args):
    try:
        logger.info('Connecting...')
        params = {
            'prefetch_count': args.prefetch_count,
            'ssl': False,
            'durable': True,
            'robust': False,
            'declare_exchange': False
        }
        if args.robust:
            status, value = _try_parse_bool(args.robust)
            if status:
                params['robust'] = value

        if args.declare_exchange:
            status, value = _try_parse_bool(args.declare_exchange)
            if status:
                params['declare_exchange'] = value

        if args.ssl:
            status, value = _try_parse_bool(args.ssl)
            if status:
                params['ssl'] = value

        if args.durable:
            status, value = _try_parse_bool(args.durable)
            if status:
                params['durable'] = value

        if args.binding_keys:
            binding_keys = [v for v in args.binding_keys.split(',') if v]
            params['binding_keys'] = binding_keys

        await consumer.create_consume_connection(**params)
    except Exception as ex:
        logger.exception(ex)
        raise


async def _run(consumer, args, stop_event: Optional[asyncio.Event] = None):
    """
    Запуск потребителя и ожидание остановки процесса.
    """
    stop_event = stop_event or asyncio.Event()

    try:
        await async_main(consumer, args)
        await stop_event.wait()
    finally:
        await consumer.close()


def main():
    logging.basicConfig(level=logging.DEBUG)

    args = parser.parse_args()

    consumer = DebugConsumer(url=args.amqp_url, exchange_name=args.exchange, exchange_type=args.exchange_type,
                             queue_name=args.queue, logger=logger)

    try:
        asyncio.run(_run(consumer, args))
    except KeyboardInterrupt:
        logger.info('Consumer stopped')


if __name__ == '__main__':
    main()
