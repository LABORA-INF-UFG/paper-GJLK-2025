import json
import random

for newUsers in [1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]:

    newTimestamp = 30

    jsonFile = json.load(open("1200_users_timestamp_{}.json".format(newTimestamp), 'r'))

    baseJsonFile = json.load(open("1200_users_timestamp_{}.json".format(newTimestamp), 'r'))

    for newUser in range(1200, newUsers):
        oldUser = random.choice(baseJsonFile["users"])
        newUserDict = oldUser.copy()
        newUserDict["ID"] = newUser
        newUserDict["game_instance"] = newUser
        jsonFile["users"].append(newUserDict)

    json.dump(jsonFile, open("{}_users_timestamp_0.json".format(newUsers), 'w'), indent=4)


    jsonGame = json.load(open("../../games/1200_users_games_timestamp_{}.json".format(newTimestamp), 'r'))
    json.dump(jsonGame, open("../../games/{}_users_games_timestamp_0.json".format(newUsers), 'w'), indent=4)