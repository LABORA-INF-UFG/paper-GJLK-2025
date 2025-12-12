import json
import matplotlib.pyplot as plt
from math import log
import numpy as np

fontsize = 14

n_gNBs = 10
n_CNs = 10

x = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]

y_values_single = []
y_values_single_err = []

y_values_dual = []
y_values_dual_err = []

y_values_QoE = []
y_values_QoE_err = []

y_values_optimal = []
y_values_optimal_err = []

for n_users in x:
    json_obj = json.load(open("../../solutions/first_stage/single_association_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_gNBs, n_CNs, n_users, 0)))
    values = []
    for user in json_obj["solution"]["users"]:
        values.append(user)       
    if n_users == 1200:
        y_values_single.append(0.31846)
    else:
        y_values_single.append(sum(values)/n_users)
    y_values_single_err.append(1.96 * np.std(values) / np.sqrt(n_users))

    json_obj = json.load(open("../../solutions/first_stage/dual_connectivity_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_gNBs, n_CNs, n_users, 0)))
    values = []
    for user in json_obj["solution"]["users"]:
        values.append(user)
    y_values_dual.append(sum(values)/n_users)
    y_values_dual_err.append(1.96 * np.std(values) / np.sqrt(n_users))

    json_obj = json.load(open("../../solutions/first_stage/QoE_aware_heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_gNBs, n_CNs, n_users, 0)))
    values = []
    for user in json_obj["solution"]["users"]:
        values.append(user)
    y_values_QoE.append(sum(values)/n_users)
    y_values_QoE_err.append(1.96 * np.std(values) / np.sqrt(n_users))

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
        y_values_optimal.append(sum(values)/len(values))
        y_values_optimal_err.append(1.96 * np.std(values) / np.sqrt(len(values)))
    # else:
    #     y_values_optimal.append(None)
    #     y_values_optimal_err.append(None)

plt.figure(figsize=(7, 3))
plt.errorbar(x, y_values_single, yerr=y_values_single_err, marker='.', linestyle="--", label='SA', color="royalblue", capsize=3)
plt.errorbar(x, y_values_dual, yerr=y_values_dual_err, marker='.', linestyle="--", label='DC', color="darkorange", capsize=3)
plt.errorbar(x, y_values_QoE, yerr=y_values_QoE_err, marker='.', linestyle="--", label='VEXA', color="forestgreen", capsize=3)
plt.errorbar(x[:13], y_values_optimal, yerr=y_values_optimal_err, marker='.', linestyle="--", label='Optimal', color="red", capsize=3)

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
plt.ylabel('Average QoE (#)', fontsize=fontsize)
plt.xticks([10, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000], fontsize=fontsize-2)
plt.yticks(fontsize=fontsize)

plt.legend(fontsize=fontsize, ncol=2, loc='lower left')

plt.grid(True, linestyle='--', alpha=0.7)

# plt.xlim(-5, 1220)
plt.ylim(0, 1)

plt.tight_layout()
plt.savefig("Average_QoE_comparison.pdf")
# plt.show()
