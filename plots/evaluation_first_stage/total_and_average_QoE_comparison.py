import json
import matplotlib.pyplot as plt
import numpy as np
from math import log

fontsize = 14

n_gNBs = 10
n_CNs = 10

x = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700]

total_single = []
total_dual = []
total_QoE = []
total_optimal = []

avg_single = []
avg_dual = []
avg_QoE = []
avg_optimal = []

err_single = []
err_dual = []
err_QoE = []
err_optimal = []

for n_users in x:
    json_obj = json.load(open("../../solutions/first_stage/single_association_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_gNBs, n_CNs, n_users, 0)))
    total_single.append(json_obj["solution"]["Total_QoE"])
    
    values = []
    for user in json_obj["solution"]["users"]:
        values.append(user)
    avg_single.append(sum(values)/len(values))
    err_single.append(1.96 * np.std(values) / np.sqrt(len(values)))

    json_obj = json.load(open("../../solutions/first_stage/dual_connectivity_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_gNBs, n_CNs, n_users, 0)))
    total_dual.append(json_obj["solution"]["Total_QoE"])

    values = []
    for user in json_obj["solution"]["users"]:
        values.append(user)
    avg_dual.append(sum(values)/len(values))
    err_dual.append(1.96 * np.std(values) / np.sqrt(len(values)))

    json_obj = json.load(open("../../solutions/first_stage/QoE_aware_heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_gNBs, n_CNs, n_users, 0)))
    total_QoE.append(json_obj["solution"]["Total_QoE"])

    values = []
    for user in json_obj["solution"]["users"]:
        values.append(user["QoE"])
    avg_QoE.append(sum(values)/len(values))
    err_QoE.append(1.96 * np.std(values) / np.sqrt(len(values)))

    if n_users <= 400:
        json_obj = json.load(open("../../solutions/first_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_gNBs, n_CNs, n_users, 0)))
        total_optimal.append(json_obj["solution"]["Total_QoE"])

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
        avg_optimal.append(sum(values)/len(values))
        err_optimal.append(1.96 * np.std(values) / np.sqrt(len(values)))
    else:
        total_optimal.append(None)

optimal_gap = []
valid_gap = []
for opt, qoe in zip(total_optimal, total_QoE):
    if opt is not None:
        gap = (opt - qoe) / opt * 100
        optimal_gap.append(gap)
        valid_gap.append(gap)
    else:
        optimal_gap.append(None)

print("Optimal gap (%):", optimal_gap)
print("Average gap:", sum(valid_gap) / len(valid_gap))

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 5), sharex=True)

plt.xticks([10, 100, 300, 500, 700, 900, 1100, 1300, 1500, 1700], fontsize=fontsize-2)
# plt.xlim(0, 1220)

color_list = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red']

# Top plot: Total QoE
ax1.set_ylabel('Total QoE (#)', fontsize=fontsize)
ax1.plot(x, total_single, marker='v', color=color_list[0], label='SA', linestyle='--')
ax1.plot(x, total_dual, marker='s', color=color_list[1], label='DC', linestyle='--')
ax1.plot(x, total_QoE, marker='o', color=color_list[2], label='VEXA', linestyle='--')
ax1.plot(x[:len(total_optimal)], total_optimal, marker='^', color=color_list[3], label='Optimal', linestyle='--')
ax1.grid(True, linestyle='--', linewidth=0.5)
ax1.set_yscale('log')
ax1.legend(fontsize=fontsize-2, loc='lower right', ncol=2)
ax1.tick_params(axis='y', labelsize=fontsize)

ax1.annotate(
    "Optimality\ngap 6%",
    xy=(300, 180), xycoords='data',
    xytext=(500, 20), textcoords='data',
    arrowprops=dict(arrowstyle="->", color='black', lw=1),
    fontsize=fontsize-2,
    color='black',
    ha='center',
    va='bottom'
)

# Bottom plot: Average QoE
ax2.set_xlabel('Number of Users (#)', fontsize=fontsize)
ax2.set_ylabel('Average QoE (#)', fontsize=fontsize)
ax2.errorbar(x, avg_single, yerr=err_single, marker='.', linestyle='--', color=color_list[0], label='SA', capsize=3)
ax2.errorbar(x, avg_dual, yerr=err_dual, marker='.', linestyle='--', color=color_list[1], label='DC', capsize=3)
ax2.errorbar(x, avg_QoE, yerr=err_QoE, marker='.', linestyle='--', color=color_list[2], label='VEXA', capsize=3)
ax2.errorbar(x[:len(avg_optimal)], avg_optimal, yerr=err_optimal, marker='.', linestyle='--', color=color_list[3], label='Optimal', capsize=3)
ax2.grid(True, which='both', linestyle='--', linewidth=0.5)
ax2.legend(fontsize=fontsize-1, ncol=2)
ax2.tick_params(axis='y')
ax2.set_ylim(0, 1)
ax2.tick_params(axis='y', labelsize=fontsize)

plt.tight_layout()
plt.savefig("Total_and_Average_QoE.pdf")
