#autoformat

from google.api_core import exceptions
from google.cloud import pubsub_v1
from flask import Flask  # import flask
import webapp2

PROJECT_ID = "bluecore-qa"


class Counter:
    BATCH_SIZE = 10

    def __init__(self):
        self.counters = dict()

    def increment(self, message):
        # used in callback
        namespace = message.attributes['namespace']
        key = message.data
        if key in self.counters:
            original = self.counters[key]
            self.counters[key] = original + 1
        else:
            self.counters[key] = 1

        message.ack()
        self._update_redis(key)
        print 'incremented counters for namespace {} and key {}: {}'.format(
            namespace, key, self.counters)

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
            print 'incremented counters for namespace {} and key {}: {}'.format(
                namespace, key, self.counters)

    def reset_counters(self):
        # call after redis updated
        self.counters = dict()

    def _reset_counter(self, key):
        if key in self.counters:
            self.counters[key] = 0

    def _update_redis(self, key):
        if self.counters[key] >= self.BATCH_SIZE:
            self._reset_counter(key)
            # update redis


class PullManager:
    def __init__(self, client, subscription_path):
        self.client = client
        self.subscription_path = subscription_path
        self.future = None
        self.max_messages = 10
        self.messages = []

    def open(self, callback):
        self.future = self.client.subscribe(self.subscription_path,
                                            callback=callback)

        return self.future

    def listen(self):
        print("Listening for messages on {}..\n".format(
            self.subscription_path))
        try:
            self.future.result(timeout=2000)
        except:
            self.future.cancel()

    def close(self):
        self.future.cancel()

    def pull(self):
        try:
            response = self.client.pull(subscription=self.subscription_path,
                                        max_messages=self.max_messages,
                                        return_immediately=True)
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
        manager = PullManager(client=self, subscription_path=subscription_path)

        return manager


def run():
    subscriber = Subscriber()
    counter = Counter()
    subscription_path = subscriber.subscription_path(PROJECT_ID, "hackathon")
    manager = subscriber.subscribe_to_topic(subscription_path)
    future = manager.open(counter.increment)
    manager.listen()


app = Flask(__name__)  # create an app instance


@app.route("/")  # at the end point /
def hello():  # call method hello
    return "Hello World!"  # which returns "hello world"


if __name__ == "__main__":  # on running python app.py
    app.run()
