import matplotlib.pyplot as plt
import sys
import json
from statistics import mean
from statistics import stdev

fontsize = 16
linewidth = 2

n_CNs = int(sys.argv[1])
n_gNBs = int(sys.argv[2])
n_users = int(sys.argv[3])

x = [_ for _ in range(0, 100)]

y_optimal = []
y_unconstrained = []
y_single_path = []

y_optimal_std = []
y_unconstrained_std = []
y_single_path_std = []

for timestamp in x:
    users_latency = []
    json_obj = json.load(open("../../solutions/second_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp), 'r'))
    users = json_obj["solution"]["users"]
    for user in users:
        users_latency.append(users[user]["max_latency"] * 1000)
    y_optimal.append(mean(users_latency))
    y_optimal_std.append(stdev(users_latency))

    users_latency = []
    json_obj = json.load(open("../../solutions/second_stage/single_path_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp), 'r'))
    users = json_obj["solution"]["users"]
    for user in users:
        users_latency.append(users[user]["max_latency"] * 1000)
    y_single_path.append(mean(users_latency))
    y_single_path_std.append(stdev(users_latency))

    users_latency = []
    json_obj = json.load(open("../../solutions/second_stage/unconstrained_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp), 'r'))
    users = json_obj["solution"]["users"]
    for user in users:
        users_latency.append(users[user]["max_latency"] * 1000)
    y_unconstrained.append(mean(users_latency))
    y_unconstrained_std.append(stdev(users_latency))
    
plt.figure(figsize=(10, 4))
plt.plot(x, y_optimal, label="Optimal", linestyle='-', color="blue", linewidth=linewidth)
plt.fill_between(x, [y - e for y, e in zip(y_optimal, y_optimal_std)], 
                    [y + e for y, e in zip(y_optimal, y_optimal_std)], 
                    color="blue", alpha=0.2)
plt.fill_between(x, [y - e for y, e in zip(y_single_path, y_single_path_std)], 
                    [y + e for y, e in zip(y_single_path, y_single_path_std)], 
                    color="orange", alpha=0.2)
plt.fill_between(x, [y - e for y, e in zip(y_unconstrained, y_unconstrained_std)], 
                    [y + e for y, e in zip(y_unconstrained, y_unconstrained_std)], 
                    color="firebrick", alpha=0.2)
plt.plot(x, y_single_path, label="Single Path", linestyle='-', color="orange", linewidth=linewidth)
plt.plot(x, y_unconstrained, label="Unconstrained", linestyle='-', color="firebrick", linewidth=linewidth)
#plt.yscale("log")
plt.xlabel("Timestamp (#)", fontsize=fontsize)
plt.ylabel("Average latency (ms)", fontsize=fontsize)
plt.xlim(0, 100)
plt.ylim(0, 40)
# plt.legend()
plt.xticks(fontsize=fontsize)
plt.yticks(fontsize=fontsize)
plt.grid(True, linestyle='--', linewidth=1)

plt.legend(loc='upper center', bbox_to_anchor=(0.606, 1.2), fontsize=fontsize, ncols=3)

plt.tight_layout()
plt.savefig("comparing_avg_latency_std.pdf")
# plt.show()