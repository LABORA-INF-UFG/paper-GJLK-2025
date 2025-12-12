import json
import matplotlib.pyplot as plt

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
    y_values_single.append(json_obj["solution"]["time"] * 1000)

    json_obj = json.load(open("../../solutions/first_stage/dual_connectivity_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_gNBs, n_CNs, n_users, 0)))
    y_values_dual.append(json_obj["solution"]["time"] * 1000)

    json_obj = json.load(open("../../solutions/first_stage/QoE_aware_heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_gNBs, n_CNs, n_users, 0)))
    y_values_QoE.append(json_obj["solution"]["time"] * 1000)

    if n_users <= 400:
        json_obj = json.load(open("../../solutions/first_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_gNBs, n_CNs, n_users, 0)))
        y_values_optimal.append(json_obj["solution"]["time"] * 1000)
    elif n_users == 500:
        y_values_optimal.append(86400000)
    else:
        y_values_optimal.append(None)

plt.figure(figsize=(6, 3))
plt.plot(x, y_values_single, marker='v', linestyle="--", label='SA', color="royalblue")
plt.plot(x, y_values_dual, marker='s', linestyle="--", label='DC', color="darkorange")
plt.plot(x, y_values_QoE, marker='o', linestyle="--", label='VEXA', color="forestgreen")
plt.plot(x, y_values_optimal, marker='^', linestyle="--", label='Optimal', color="red")

plt.yscale('log')

plt.xlabel('Number of Users (#)', fontsize=fontsize)
plt.ylabel('Time (ms)', fontsize=fontsize)
plt.xticks([10, 100, 300, 500, 700, 900, 1100, 1300, 1500, 1700], fontsize=fontsize-3.5)
plt.yticks(fontsize=fontsize)

plt.legend(fontsize=fontsize, ncol=2, loc='upper right')

plt.grid(True, linestyle='--', alpha=0.7)

# plt.xlim(-5, 1220)
# plt.ylim(0, 10**3)

plt.tight_layout()
plt.savefig("Time_comparison.pdf")
# plt.show()
