import matplotlib.pyplot as plt
import sys
import json

fontsize = 16
linewidth = 2

n_CNs = int(sys.argv[1])
n_gNBs = int(sys.argv[2])
n_users = int(sys.argv[3])

x = [_ for _ in range(0, 100)]

y_optimal = []
y_unconstrained = []
y_single_path = []

for timestamp in x:
    json_obj = json.load(open("../../solutions/second_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp), 'r'))
    y_optimal.append(json_obj["solution"]["time"] * 1000)
    json_obj = json.load(open("../../solutions/second_stage/single_path_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp), 'r'))
    y_single_path.append(json_obj["solution"]["time"] * 1000)
    json_obj = json.load(open("../../solutions/second_stage/unconstrained_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_gNBs, n_users, timestamp), 'r'))
    y_unconstrained.append(json_obj["solution"]["time"] * 1000)
    
plt.figure(figsize=(10, 4))
plt.plot(x, y_optimal, label="Optimal", linestyle='-', color="blue", linewidth=linewidth)
plt.plot(x, y_single_path, label="Single Path", linestyle='-', color="orange", linewidth=linewidth)
plt.plot(x, y_unconstrained, label="Unconstrained", linestyle='-', color="firebrick", linewidth=linewidth)
plt.yscale("log")
plt.xlabel("Timestamp (#)", fontsize=fontsize)
plt.ylabel("Solve Time (ms)", fontsize=fontsize)
plt.xlim(0, 100)
plt.ylim(0, 10**6)
# plt.legend()
plt.yticks(fontsize=fontsize)
plt.xticks([_ for _ in range(0, 101, 10)], fontsize=fontsize)
plt.grid(True, linestyle='--', linewidth=1)

plt.legend(loc='upper center', bbox_to_anchor=(0.613, 1.2), fontsize=fontsize, ncols=3)

plt.tight_layout()
plt.savefig("comparing_solve_time.pdf")
# plt.show()