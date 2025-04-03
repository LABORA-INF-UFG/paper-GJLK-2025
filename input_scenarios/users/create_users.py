import random
import json
import sys

random.seed(5)

n_users = int(sys.argv[1])

json_dict = {"users": []}

if n_users == 2: # 2 users in a FPS game
    users_app = []
    for i in range(0, 1):
        users_app.append(i)
        users_app.append(i)

if n_users == 3: # 2 users in a FPS game 1 user in SP game
    users_app = []
    for i in range(0, 1):
        users_app.append(i)
        users_app.append(i)
    for i in range(1, 2):
        users_app.append(i)

if n_users == 4: # 2 users in a FPS game 2 users in SP game
    users_app = []
    for i in range(0, 1):
        users_app.append(i)
        users_app.append(i)
    for i in range(1, 3):
        users_app.append(i)

elif n_users == 5: # 2 users in a FPS game, 2 players in FG game and 1 player in SP game
    users_app = [0, 0, 1, 1, 2]

elif n_users == 6: # 2 users in a FPS game, 2 players in FG game and 2 players in SP game
    users_app = [0, 0, 1, 1, 2, 3]

elif n_users == 7: # 2 users in a FPS game, 2 players in FG game and 3 players in SP game
    users_app = [0, 0, 1, 1, 2, 3, 4]

elif n_users == 8: # 4 users in a FPS game, 2 players in FG game and 2 players in SP game
    users_app = [0, 0, 1, 1, 2, 2, 3, 4]

elif n_users == 9: # 4 users in a FPS game, 2 players in FG game and 3 players in SP game
    users_app = [0, 0, 1, 1, 2, 2, 3, 4, 5]

elif n_users == 10:
    users_app = [0, 0, 0, 0, 1, 1, 2, 2, 3, 4]






elif n_users == 20:
    users_app = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 7, 8, 9]
elif n_users == 40:
    users_app = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3,
                 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11,
                 12, 13, 14, 15, 16, 17, 18, 19]
elif n_users == 80:
    users_app = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7,
                 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14, 14, 15, 15, 16, 16, 17, 17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 22, 23, 23,
                 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39]
elif n_users == 160:
    users_app = []
    for i in range(0, 8):
        users_app.append(i)
        users_app.append(i)
        users_app.append(i)
        users_app.append(i)
        users_app.append(i)
        users_app.append(i)
        users_app.append(i)
        users_app.append(i)
    for i in range(8, 40):
        users_app.append(i)
        users_app.append(i)
    for i in range(40, 72):
        users_app.append(i)

for i in range(0, n_users):
    json_dict["users"].append({
        "ID": i,
        "device": {
            "resolution": random.choice(["2k", "4k", "8k"]),
            "fps": random.choice([30, 60, 90])
            },
        "application_ID": users_app[i],
        "SINR": [{
            "BS_ID": bs,
            "SINR": random.randint(25, 30)
        } for bs in range(0, 12)]
    })

json.dump(json_dict, open("{}_users.json".format(n_users), "w"), indent=4)