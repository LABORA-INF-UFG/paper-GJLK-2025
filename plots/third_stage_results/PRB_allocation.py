import json
import matplotlib.pyplot as plt
import numpy as np
from math import log

x = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700]

fontsize = 14

y_MTPsched = []
y_RR = []
y_optimal = []

y_PRBs_RR = []
y_PRBs_MTPsched = []
y_PRB_optimal = []

y_PF = [0.15, 0.75, 1.5666666666666667, 2.0, 2.4, 3.1166666666666667, 3.6714285714285713, 3.95, 4.477777777777778, 4.65, 19.305, 48.346666666666664, 39.20375, 58.093, 69.38666666666667, 81.71857142857142, 92.91125, 104.00777777777778, 114.8235, 125.99045454545454, 136.41125, 561.7273076923077, 588.7857142857143, 615.154, 639.6853125, 654.2341176470588, 672.1061111111111, 679.2821052631579, 701.611]

resolution_to_integer = {"1080p": 1, "2K": 2, "4K": 3}

users_number_of_objects = {}

for n_users in x:
    if n_users < 700:
        json_obj = json.load(open("../../solutions/third_stage/AMPS_MTPsched/{}_CNs_{}_gNBs_{}_users.json".format(10, 10, n_users), 'r'))
        user_received_PRBs = {}
        users_MTP = []
        MTP_sched_latency = []
        MTPsched_PRBs = 0
        for user in json_obj["solution"]["users"]:
            user_received_PRBs[user["ID"]] = 0
            PRBs = user["received_PRBs_in_TTI_per_gNB"]
            for gNB in PRBs:
                gNB_ID = gNB["gNB"]
                TTIs = gNB["TTIs"]
                for t in TTIs:
                    user_received_PRBs[user["ID"]] += TTIs[t]
            max_MTP = 0
            MTPsched_PRBs += user_received_PRBs[user["ID"]]
            other_MTP = (n_users - 1) * 0.5
            users_MTP.append(max_MTP + other_MTP)
            MTP_sched_latency.append(user["MTP_latency"])
    
    optimal_users_MTP = {}
    if n_users <= 100:
        json_obj = json.load(open("../../solutions/third_stage/optimal_model/{}_CNs_{}_gNBs_{}_users.json".format(10, 10, n_users), 'r'))
        optimal_PRBs = 0
        for user in json_obj["solution"]["users"]:
            for gNB in user["received_PRBs_in_TTI_per_gNB"]:
                gNB_ID = gNB["gNB"]
                TTIs = gNB["TTIs"]
                TTIs_transmitted = []
                for t in TTIs:
                    optimal_PRBs += TTIs[t]
                    TTIs_transmitted.append(int(t))
                
                optimal_users_MTP[user["ID"]] = 0
                
                for i in range(len(TTIs_transmitted)):
                    if i + 1 < len(TTIs_transmitted):
                        mtp_user_calc = (TTIs_transmitted[i + 1] - TTIs_transmitted[i]) * 0.5
                        if mtp_user_calc > optimal_users_MTP[user["ID"]]:
                            optimal_users_MTP[user["ID"]] = mtp_user_calc
                print(f"User {user['ID']} MTP: {optimal_users_MTP[user['ID']]}")
        avg_optimal_mtp = sum(optimal_users_MTP.values()) / len(optimal_users_MTP) if optimal_users_MTP else 0
        print(f"Average optimal MTP: {avg_optimal_mtp}")
        y_optimal.append(avg_optimal_mtp)
        y_PRB_optimal.append(optimal_PRBs / (56 * 2000))

                

    
    
    y_RR.append(sum(users_MTP)/len(users_MTP))
    y_MTPsched.append(sum(MTP_sched_latency)/len(MTP_sched_latency))
    y_PRBs_MTPsched.append(MTPsched_PRBs/(56 * 2000))
    y_PRBs_RR.append(1)

# x = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]

fig, ax = plt.subplots(figsize=(7, 3))

ax.set_yscale('log')
ax.axhline(y=50, color='red', linestyle='--', linewidth=1.5)
ax.plot(x, y_RR, marker='s', label='Round-Robin', linestyle='-', linewidth=2, color="tab:orange")
ax.plot(x, y_MTPsched, marker='o', label='MTPsched', linestyle='-', linewidth=2, color="forestgreen")
ax.plot(x[:10], y_optimal, marker='^', label='Optimal', linestyle='-', linewidth=2, color="red")
ax.plot(x, y_PF[:len(x)], marker='x', label='Proportional Fair', linestyle='-', linewidth=2, color="blue")
ax.set_ylabel('Avg. MTP latency (ms)', fontsize=fontsize)
ax.legend(fontsize=fontsize, loc='lower right')
ax.grid(True, linestyle='--', alpha=0.7)
ax.annotate(
    '50 ms',
    xy=(34, 50), xycoords='data',
    xytext=(80, 100), textcoords='data',
    arrowprops=dict(arrowstyle="->", color='black', lw=2),
    fontsize=fontsize-1,
    color='black',
    ha='center',
    va='bottom'
)

plt.xlabel('Number of Users (#)', fontsize=fontsize)
plt.xticks([0, 100, 300, 500, 700, 900, 1100, 1300, 1500, 1700], fontsize=fontsize)
plt.yticks(fontsize=fontsize)
ax.set_xlim(0, 1710)
plt.tight_layout()
plt.savefig("MTP_latency_compare.pdf")

fig2, ax2 = plt.subplots(figsize=(7, 3))

bar_width = 0.28
indices = np.arange(len(x))

ax2.bar(indices, y_PRBs_RR, bar_width, label='Round-Robin', color="tab:orange")
ax2.bar(indices + bar_width, y_PRBs_MTPsched, bar_width, label='MTPsched', color="forestgreen")
ax2.bar(indices[:10] + 2 * bar_width, y_PRB_optimal, bar_width, label='Optimal', color="red")

ax2.set_yscale('log')
ax2.set_xlabel('Number of Users (#)', fontsize=fontsize)
ax2.set_ylabel('PRBs usage (log)', fontsize=fontsize)
ax2.set_xticks(indices + bar_width / 2)
ax2.set_xticklabels(x, fontsize=fontsize)
ax2.set_yticklabels([' ', ' %', '1%', '10%', '100%'], fontsize=fontsize)
ax2.legend(fontsize=fontsize, ncol=3, bbox_to_anchor=(0.51, 1.3), loc='upper center')
ax2.grid(True, linestyle='--', alpha=0.7)
plt.yticks(fontsize=fontsize)
plt.tight_layout()
plt.savefig("PRBs_usage_compare.pdf")