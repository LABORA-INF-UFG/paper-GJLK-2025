import json
import random

nUsers= 1300

jsonFile = json.load(open("1200_users_games_timestamp_70.json", 'r'))

newTimestamp = random.randint(0, 99)

baseJsonFile = json.load(open("1200_users_games_timestamp_{}.json".format(newTimestamp), 'r'))

for newUser in range(1200, nUsers):
    oldUser = random.choice(baseJsonFile["games"])
    baseJsonFile["games"].append(oldUser)

json.dump(baseJsonFile, open("{}_users_games_timestamp_0.json".format(nUsers), 'w'), indent=4)