import json
import matplotlib.pyplot as plt

tamanho_fonte = 12

my_list = []
C7_list = []

for user in range(1, 17):
    json_obj = json.load(open("../{}_users_4_BSs_2_MEC_solution.json".format(user), 'r'))
    my_count = 0
    for i in json_obj["Solution"]["Users_QoE"]:
        if json_obj["Solution"]["Users_QoE"][i] > 0:
            my_count += 1
    my_list.append(my_count/user)
    
    json_obj = json.load(open("../C7_{}_users_4_BSs_2_MEC_solution.json".format(user), 'r'))
    C7_count = 0
    for i in json_obj["Solution"]["Users_QoE"]:
            if json_obj["Solution"]["Users_QoE"][i] > 0:
                C7_count += 1
    C7_list.append(C7_count/user)

# Prepare data for plotting
users = list(range(1, 17))

# Plot the data
plt.figure(figsize=(7, 2))
plt.plot(users, my_list, label='VR-GX', marker='o', linestyle='--', linewidth = 1.5)
plt.plot(users, C7_list, label='Du [15]', marker='o', linestyle='--', linewidth = 1.5)

plt.ylim(0, 1.1)

plt.yticks([0, 0.2, 0.4, 0.6, 0.8, 1], ['0', '20', '40', '60', '80', '100'], fontsize=tamanho_fonte)
plt.xticks([i for i in range(1, 17)], fontsize=tamanho_fonte)

# Add titles and labels
plt.xlabel('Users (#)', fontsize=tamanho_fonte)
plt.ylabel('Admitted users (#)', fontsize=tamanho_fonte-0.5)
plt.legend(fontsize=tamanho_fonte, ncols=2, loc='lower left')
plt.grid(True)

plt.savefig('admission.png', bbox_inches='tight')