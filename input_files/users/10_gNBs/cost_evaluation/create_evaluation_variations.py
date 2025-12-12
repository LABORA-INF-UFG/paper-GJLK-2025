import json
import random

random.seed(42)

users = [400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]

CQI_mapping = [0.1523, 0.3770, 0.8770, 1.4766, 1.9141, 2.4063, 2.7305, 3.3223, 3.9023, 4.5234, 5.1152, 5.5547]

for tti in range(1, 30):
    for n_users in [400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]:
        json_original = json.load(open("{}_users_timestamp_0.json".format(n_users), "r"))

        users = json_original["users"]
        for user in users:
            for se in user["SE"]:
                user["SE"][se] = random.choice(CQI_mapping)

        json.dump(json_original, open("{}_users_timestamp_{}.json".format(n_users, tti), "w"), indent=4)