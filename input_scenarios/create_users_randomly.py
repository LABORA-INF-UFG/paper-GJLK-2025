import json
import random
import sys

random.seed(10)

def create_users_randomly(n_users, n_BSs):
    n_devices = ["2k", "4k", "8k"]
    users = []
    for i in range(n_users):
        user = {}
        user["ID"] = i
        user["device"] = {"resolution": random.choice(n_devices), "fps": 90}
        user["application_ID"] = random.randint(0, int(n_users/3))
        user["SINR"] = [{"BS_ID": bs, "SINR": random.randint(5, 25)} for bs in range(0, n_BSs)]
        users.append(user)
    return users

if __name__ == "__main__":
    n_users = int(sys.argv[1])
    n_BSs = int(sys.argv[2])
    file_name = int(sys.argv[3])
    users = create_users_randomly(n_users, n_BSs)
    with open("../input_scenarios/users_{}.json".format(file_name), 'w') as f:
        json.dump({"users": users}, f, indent=4)