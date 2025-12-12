import os

x = [400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]

for n_users in x:
    # os.system("python3 single_association_QoE_aware.py 10 10 {}".format(n_users))
    # os.system("python3 dual_connectivity_QoE_aware.py 10 10 {}".format(n_users))
    os.system("python3 QoE_aware_many_to_many_heuristic.py 10 10 {}".format(n_users))