import os

for user in [400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]:
    os.system("python3 first_stage_linear.py 10 10 {}".format(user))