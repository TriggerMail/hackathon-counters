#autoformat

from google.api_core import exceptions
from google.cloud import pubsub_v1

PROJECT_ID = "bluecore-qa"


class Counter:
    def __init__(self):
        self.counters = dict()

    def increment(self, namespace, key):
        if key in self.counters:
            original = self.counters[key]
            self.counters[key] = original + 1
        else:
            self.counters[key] = 1

        print 'incremented counters for namespace {} and key {}: {}'.format(namespace, key, self.counters)

    def batch_increment(self, received_messages):
        for message in received_messages:
            namespace = message.message.attributes['namespace']
            key = message.message.data

            if key in self.counters:
                original = self.counters[key]
                self.counters[key] = original + 1
            else:
                self.counters[key] = 1
            # message.ack()
            print 'incremented counters for namespace {} and key {}: {}'.format(namespace, key,
                                                                                self.counters)

    def reset_counters(self):
        # call after redis updated
        self.counters = dict()


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
        print("Listening for messages on {}..\n".format(self.subscription_path))

        return self.future

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
counter = Counter()


def callback(message):
    # counter.increment(message.attributes.namespace, message.data) - throws error
    # message.ack()
    return


subscription_path = subscriber.subscription_path(PROJECT_ID, "hackathon")
manager = subscriber.subscribe_to_topic(subscription_path)
future = manager.open(callback)

try:
    messages = manager.pull()
    counter.batch_increment(messages)
except:  # noqa
    future.cancel()
