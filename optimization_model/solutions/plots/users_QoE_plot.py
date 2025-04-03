import json
import matplotlib.pyplot as plt
import time

plt.figure(figsize=(10, 4))

# Number of users
n_users = [2, 3, 4, 5, 6, 7, 8, 9, 10]

for user in n_users:
    qoe_values = []
    json_obj = json.load(open("../{}_users_4_BSs_2_MEC_solution.json".format(user)))
    for i in json_obj["Solution"]["Users_QoE"].values():
        qoe_values.append(i)

    C7_qoe_values = []
    json_obj = json.load(open("../C7_{}_users_4_BSs_2_MEC_solution.json".format(user)))
    for i in json_obj["Solution"]["Users_QoE"].values():
        C7_qoe_values.append(i)
    # Generate user IDs
    user_ids = ["User {}".format(i + 1) for i in range(0, user)]

    plt.grid(True, axis="y", linestyle='--', alpha=0.8)

    # Create the bar plot
    bar_width = 0.35
    index = range(len(user_ids))
    
    plt.bar([i - bar_width/2 for i in index], qoe_values, bar_width, color='navy', label='QoE')
    plt.bar([i + bar_width/2 for i in index], C7_qoe_values, bar_width, color='firebrick', label='C7 QoE')
    
    # plt.legend(fontsize=16)
    
    plt.yticks(fontsize=16)
    plt.xticks([i for i in range(0, len(user_ids))], ["User {}".format(i+1) for i in range(0, len(user_ids))], fontsize=16)
    plt.ylabel('QoE (#)', fontsize=16)

    # Add labels and title
    plt.tight_layout()
    plt.savefig('{}_users_QoE_plot.pdf'.format(user), bbox_inches='tight')