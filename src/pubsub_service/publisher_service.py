#autoformat
from google.cloud import pubsub_v1
import sys
import time
import http.server
import socketserver

publisher = pubsub_v1.PublisherClient()
# The `subscription_path` method creates a fully qualified identifier
# in the form `projects/{project_id}/subscriptions/{subscription_name}`

topic_path = publisher.topic_path("bluecore-qa", "hackathon")
print("Publishing messagesto {}..\n".format(topic_path))

# result() in a future will block indefinitely if `timeout` is not set,
# unless an exception is encountered first.
try:
    while True:
        data = "trish was here"
        future = publisher.publish(
            topic_path,
            data=data.encode("utf-8")  # data must be a bytestring.
        )
        print("Topic created: {}".format(future))
        time.sleep(1)
except Exception as e:  # noqa
    print("{}".format(e))
    sys.exit()
