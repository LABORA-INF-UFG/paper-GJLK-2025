import os

x = [900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]

for n_users in x:
    os.system("python3 second_stage_MILP.py 10 10 {}".format(n_users))
