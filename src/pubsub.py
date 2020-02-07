#autoformat
import random
import logging
from bluecore import bluecore_redis
from google.api_core import exceptions
from google.cloud import pubsub_v1

PROJECT_ID = "bluecore-qa"


class MasterNotFoundError(object):
    pass


class Redis:
    SERAPIAN_METADATA_COLLECTION_NAME = 'serapian_metadata_run'
    SERAPIAN_METADATA_SCHEMA_NAME = 'serapian_metadata_run'
    REDIS_SERAPIAN_METADATA_COLLECTION_NAME = 'redis_serapian_metadata_run'
    REDIS_SERAPIAN_METADATA_SCHEMA_NAME = 'redis_serapian_metadata_run'
    REDIS_OPERATIONS_SHARD_COUNT = 40
    REDIS_OPERATIONS_QUEUE_NAMES = [
        'redis-operations-%s' % i for i in range(REDIS_OPERATIONS_SHARD_COUNT)
    ]

    def __init__(self):
        self.instance = None

    def validate(self):
        self.instance = bluecore_redis.get_bluecore_redis_instance()

    @property
    def queue_name(self):
        return random.choice(self.REDIS_OPERATIONS_QUEUE_NAMES)

    def _update_count(self, redis_key, delta):
        try:
            self.instance.incr(redis_key, amount=delta)
            # set expiration only before we send data to bigquery
            # self.instance.expire(key, 100000)
        except MasterNotFoundError:
            logging.exception(
                u"Could not acquire redis master instance to increment redis key {}; rescheduling"
                .format(redis_key)
            )
            """
            reschedule here 
            countdown = float(random.randint(0, self.RESCHEDULE_DELAY))
            self.schedule(countdown=countdown)
            """
        except Exception:
            logging.exception(u'Could not increment redis key {}'.format(redis_key))
            raise

    def update(self, counters):
        for k, v in counters:
            self._update_count(k, v)


class Counter:
    BATCH_SIZE = 10

    def __init__(self, pull_manager):
        self.counters = dict()
        self.pull_manager = pull_manager
        self.redis_instance = Redis()

    def increment(self, message):
        # used in callback
        namespace = message.attributes['namespace']
        key = message.data
        if key in self.counters:
            original = self.counters[key]
            self.counters[key] = original + 1
        else:
            self.counters[key] = 1

        self.pull_manager.messages.append(message)
        message.ack()
        self._update_redis()
        print 'incremented counters for namespace {} and key {}: {}'.format(namespace, key, self.counters)

    def batch_increment(self, received_messages):
        # can be used when using PullManager.pull
        for message in received_messages:
            namespace = message.message.attributes['namespace']
            key = message.message.data

            if key in self.counters:
                original = self.counters[key]
                self.counters[key] = original + 1
            else:
                self.counters[key] = 1
            message.ack()
            print 'incremented counters for namespace {} and key {}: {}'.format(namespace, key,
                                                                                self.counters)

    def _reset_counters(self):
        # call after redis updated
        self.counters = dict()

    def _reset_counter(self, key):
        if key in self.counters:
            self.counters[key] = 0

    def _update_redis(self):
        if len(self.pull_manager.messages) % self.BATCH_SIZE == 0:
            self.redis_instance.update(self.counters)
            self._reset_counters()


class PullManager:
    def __init__(self, client, subscription_path):
        self.client = client
        self.subscription_path = subscription_path
        self.future = None
        self.max_messages = 10
        self.messages = []

    def open(self, callback):
        self.future = self.client.subscribe(
            self.subscription_path, callback=callback
        )

        return self.future

    def listen(self):
        print("Listening for messages on {}..\n".format(self.subscription_path))
        try:
            self.future.result(timeout=2000)
        except:
            self.future.cancel()

    def close(self):
        self.future.cancel()

    def pull(self):
        try:
            response = self.client.pull(
                subscription=self.subscription_path,
                max_messages=self.max_messages,
                return_immediately=True
            )
            messages = response.received_messages
            self.messages += messages
        except exceptions.DeadlineExceeded:
            messages = []

        print 'pulled {} messages'.format(len(messages))
        return messages

    def _ack_messages(self):
        for message in self.messages:
            print "received message {}".format(message)
            message.ack()


class Subscriber(pubsub_v1.SubscriberClient):
    def subscribe_to_topic(self, subscription_path):
        manager = PullManager(
            client=self,
            subscription_path=subscription_path
        )

        return manager


subscriber = Subscriber()
subscription_path = subscriber.subscription_path(PROJECT_ID, "hackathon")
manager = subscriber.subscribe_to_topic(subscription_path)
counter = Counter(manager)
future = manager.open(counter.increment)
manager.listen()
