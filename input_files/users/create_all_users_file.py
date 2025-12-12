import os

n_Users = 1000

for i in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]:# range(2, n_Users, 2):
    os.system("python3 create_users_file.py {} {}".format(10, i))