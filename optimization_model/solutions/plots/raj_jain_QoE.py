import json
import matplotlib.pyplot as plt

tamanho_fonte = 12

def raj_jain_fairness(latencies):
    n = len(latencies)
    sum_latencies = sum(latencies)
    sum_latencies_squared = sum(latencies_i ** 2 for latencies_i in latencies)
    fairness_index = (sum_latencies ** 2) / (n * sum_latencies_squared)
    return fairness_index

my_list = {}
C7_list = {}

for user in range(1, 17):
    if user in range(1, 6):
        json_obj = json.load(open("../{}_users_4_BSs_2_MEC_solution.json".format(user), 'r'))
    else:
        json_obj = json.load(open("../Heuristic_{}_users_4_BSs_2_MEC_solution.json".format(user), 'r'))
    
    my_list[user] = []

    for i in json_obj["Solution"]["Users_QoE"]:
        my_list[user].append(json_obj["Solution"]["Users_QoE"][i])
    
    json_obj = json.load(open("../C7_{}_users_4_BSs_2_MEC_solution.json".format(user), 'r'))
    
    C7_list[user] = []

    for i in json_obj["Solution"]["Users_QoE"]:
        C7_list[user].append(json_obj["Solution"]["Users_QoE"][i])

    # Calculate Raj Jain fairness index for each list
    my_list_fairness = raj_jain_fairness(my_list)
    C7_list_fairness = raj_jain_fairness(C7_list)

    # Print the results
    print(f"Raj Jain fairness index for my_list: {my_list_fairness}")
    print(f"Raj Jain fairness index for c7_list: {C7_list_fairness}")


# Prepare data for plotting
users = list(range(1, 17))
my_list_fairness_values = [raj_jain_fairness(my_list[user]) for user in users]
C7_list_fairness_values = [raj_jain_fairness(C7_list[user]) for user in users]

# Plot the data
plt.figure(figsize=(7, 2))
plt.plot(users, my_list_fairness_values, label='VR-GamingX', marker='o', linestyle='--', linewidth = 1.5)
plt.plot(users, C7_list_fairness_values, label='Du [10]', marker='o', linestyle='--', linewidth = 1.5)

plt.ylim(0, 1.1)

plt.xticks([i for i in range(1, 17)], fontsize=tamanho_fonte)
plt.yticks([0, 0.2, 0.4, 0.6, 0.8, 1], ['0', '20', '40', '60', '80', '100'], fontsize=tamanho_fonte)

# Add titles and labels
plt.xlabel('Users (#)', fontsize=tamanho_fonte)
plt.ylabel('QoE Fairness (%)', fontsize=tamanho_fonte)
# plt.legend(fontsize=tamanho_fonte, ncols=2, loc='upper right')
plt.grid(True)

plt.savefig('raj_jain_QoE.png', bbox_inches='tight')