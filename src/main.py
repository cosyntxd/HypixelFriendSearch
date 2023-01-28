import requests
import collections
import pickle
import time
import os

# Tested to be slightly more efficient
session = requests.Session()

class Node:
    def __init__(self, data, prev=None):
        self.uuid = data
        self.prev = prev

    def __repr__(self):
        return "{} > {}".format(self.uuid, self.prev)


class InputError(Exception):
    def __init__(self, str=""):
        self.str = "\033[91m{}\033[0m".format(str)

    def __str__(self):
        return self.str


if os.name == "nt":
    os.system("color")


api_key = input("API key: ").strip()
if len(api_key) != 36:
    raise InputError("Key must be 36 characters long")

speed = input("requests per minute: ").strip()
try:
    speed = int(speed)
except ValueError:
    raise InputError("Speed must be an integer")

uuid_self = input("UUID of self: ").strip()
if len(uuid_self) != 32:
    raise InputError("UUID must be 32 characters long")

uuid_target = input("UUID of target: ").strip()
if len(uuid_target) != 32:
    raise InputError("UUID must be 32 characters long")

save_file = "hfs.save"

if os.path.exists(save_file) and os.path.getsize(save_file) > 1:
    with open(save_file, "rb") as f:
        [iterations, to_process, check_map, node_tree] = pickle.load(f)
else:
    iterations = 0
    node_tree = Node(uuid_self)
    to_process = collections.deque([node_tree])
    check_map = {}

with open(save_file, "wb") as f:
    while to_process:
        iterations += 1

        print(f"{iterations} api calls, {len(to_process)} players known, {len(check_map)} processed")

        time.sleep(60 / float(speed))

        friend = to_process.popleft()
        if check_map.get(friend.uuid):
            continue

        api_request = session.get(
            "https://api.hypixel.net/friends",
            params = {"key": api_key, "uuid": friend.uuid},
        )
        if api_request.status_code != 200:
            print(api_request.json())
            print(f"API returned with status code {api_request.status_code} because {api_request.json()['cause']}")
            # Retry by adding the node back to front of queue
            to_process.appendleft(friend)
            continue

        for friend_request in api_request.json()["records"]:
            if friend_request["uuidSender"] == friend.uuid:
                person = friend_request["uuidReceiver"]
            else:
                person = friend_request["uuidSender"]

            person_node = Node(person, prev=friend)

            if person == uuid_target:
                print(person_node)
                exit()

            to_process.append(person_node)
            check_map[friend] = True

        # Saves around every 8-9 minutes at 120/m
        if iterations % 1000 == 0:
            pickle.dump([iterations, to_process, check_map, node_tree], f)