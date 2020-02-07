import redis
# connect with redis server as Bob
bob_r = redis.Redis(host='localhost', port=6379, db=0)
# subscribe to hackathon
bob_p = bob_r.subscribe('hackathon')

messages = []
message = bob_p.get_message()
key = message['data']

messages.append(message)
if len(messages) > 5:
    bob_r.incr(key, amount=len(bob_p))
    messages = []
