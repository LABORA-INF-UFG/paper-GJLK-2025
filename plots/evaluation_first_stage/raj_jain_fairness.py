import json
import matplotlib.pyplot as plt
from math import log
import numpy as np

fontsize = 14

n_gNBs = 10
n_CNs = 10

x = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1200, 1300, 1400, 1500, 1600, 1700]

y_values_single = []
y_values_dual = []
y_values_QoE = []
y_values_optimal = []

for n_users in x:
    json_obj = json.load(open("../../solutions/first_stage/single_association_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_gNBs, n_CNs, n_users, 0)))
    values = []
    for user in json_obj["solution"]["users"]:
        values.append(user)
    # Calculate Raj Jain Fairness Index
    numerator = (sum(values))**2
    denominator = len(values) * sum([v**2 for v in values])
    fairness_index = numerator / denominator if denominator != 0 else 0
    y_values_single.append(fairness_index)

    json_obj = json.load(open("../../solutions/first_stage/dual_connectivity_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_gNBs, n_CNs, n_users, 0)))
    values = []
    for user in json_obj["solution"]["users"]:
        values.append(user)
    # Calculate Raj Jain Fairness Index
    numerator = (sum(values))**2
    denominator = len(values) * sum([v**2 for v in values])
    fairness_index = numerator / denominator if denominator != 0 else 0
    y_values_dual.append(fairness_index)

    json_obj = json.load(open("../../solutions/first_stage/QoE_aware_heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_gNBs, n_CNs, n_users, 0)))
    values = []
    for user in json_obj["solution"]["users"]:
        values.append(user)
    # Calculate Raj Jain Fairness Index
    numerator = (sum(values))**2
    denominator = len(values) * sum([v**2 for v in values])
    fairness_index = numerator / denominator if denominator != 0 else 0
    y_values_QoE.append(fairness_index)

    if n_users <= 400:
        values = []
        json_obj = json.load(open("../../solutions/first_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_gNBs, n_CNs, n_users, 0)))
        for user in json_obj["solution"]["users"]:
            if user["priority"] == "quality":
                if user["resolution"] == "1080p":
                    values.append(log(1))
                elif user["resolution"] == "2K":
                    values.append(log(2))
                elif user["resolution"] == "4K":
                    values.append(log(3))
            else:
                values.append(log(user["frame_rate"]/30))
        # Calculate Raj Jain Fairness Index
        numerator = (sum(values))**2
        denominator = len(values) * sum([v**2 for v in values])
        fairness_index = numerator / denominator if denominator != 0 else 0
        y_values_optimal.append(fairness_index)
    else:
        y_values_optimal.append(None)

plt.figure(figsize=(7, 3))
plt.plot(x, y_values_single, marker='v', linestyle="--", label='SA', color="royalblue")
plt.plot(x, y_values_dual, marker='s', linestyle="--", label='DC', color="darkorange")
plt.plot(x, y_values_QoE, marker='o', linestyle="--", label='VEXA', color="forestgreen")
plt.plot(x, y_values_optimal, marker='^', linestyle="--", label='Optimal', color="red")

# plt.annotate(
#     "Optimality\ngap 6%",
#     xy=(300, 220), xycoords='data',
#     xytext=(150, 350), textcoords='data',
#     arrowprops=dict(arrowstyle="->", color='black', lw=2),
#     fontsize=fontsize-2,
#     color='black',
#     ha='center',
#     va='bottom'
# )

# plt.yscale('log')

plt.xlabel('Number of Users (#)', fontsize=fontsize)
plt.ylabel('Raj Jain Fairness (#)', fontsize=fontsize)
plt.xticks([10, 100, 300, 500, 700, 900, 1100, 1300, 1500, 1700], fontsize=fontsize-2)
plt.yticks(fontsize=fontsize)

plt.legend(fontsize=fontsize, ncol=2, loc='lower left')

plt.grid(True, linestyle='--', alpha=0.7)

# plt.xlim(-5, 1220)
plt.ylim(0, 1.05)

plt.tight_layout()
plt.savefig("Raj_Jain_comparison.pdf")
# plt.show()
