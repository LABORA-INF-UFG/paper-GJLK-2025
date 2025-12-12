import json
import matplotlib.pyplot as plt
import numpy as np
from math import log

x = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400]

fontsize = 14

y_first_stage = []
y_third_stage = []
y_optimal = []
y_DU = []

resolution_to_integer = {"1080p": 1, "2K": 2, "4K": 3}

users_number_of_objects = {}

for n_users in x:
    json_obj = json.load(open("../../solutions/third_stage/AMPS_MTPsched/{}_CNs_{}_gNBs_{}_users.json".format(10, 10, n_users), 'r'))
    y_third_stage.append(json_obj["solution"]["Total_QoE"])
    for user in json_obj["solution"]["users"]:
        users_number_of_objects[user["ID"]] = user["number_of_objects"]

    if n_users <= 100:
        json_obj = json.load(open("../../solutions/third_stage/optimal_model/{}_CNs_{}_gNBs_{}_users.json".format(10, 10, n_users), 'r'))
        y_optimal.append(json_obj["solution"]["Total_QoE"])

    json_obj = json.load(open("../../solutions/first_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_0.json".format(10, 10, n_users), 'r'))
    qoe = 0
    qoe_DU = 0
    for user in json_obj["solution"]["users"]:
        qoe += log(resolution_to_integer[user["resolution"]]) * users_number_of_objects[user["ID"]]
        qoe_DU += (log(resolution_to_integer["1080p"]) * (users_number_of_objects[user["ID"]] * 0.75) + log(resolution_to_integer["2K"]) * (users_number_of_objects[user["ID"]] * 0.25))
    y_first_stage.append(qoe)
    y_DU.append(qoe_DU)


plt.figure(figsize=(7, 3))
plt.yscale('log')
plt.plot(x, y_third_stage, marker='o', label='AMPS', linestyle='--', linewidth=1.5, color="forestgreen")
plt.plot(x, y_first_stage, marker='s', label='VEXA', linestyle='--', linewidth=1.5, color="royalblue")
plt.plot(x[:10], y_optimal, marker='^', label='Optimal', linestyle='--', linewidth=1.5, color="red")
plt.plot(x, y_DU, marker='v', label='RCA model', linestyle='--', linewidth=1.5, color="tab:orange")
plt.xlim(0, 405)
# plt.ylim(0, 1000000)
plt.xlabel('Number of Users (#)', fontsize=fontsize)
plt.ylabel('Total QoE (#)', fontsize=fontsize)
plt.yticks(fontsize=fontsize)
plt.xticks([10, 100, 200, 300, 400], fontsize=fontsize)
plt.legend(fontsize=fontsize, loc='lower right', ncol=2)
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(f"first_stage_third_stage_QoE_{n_users}_users.pdf")
    