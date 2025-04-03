from methods import read_BSs, read_MEC, read_users
from model import run_model
import sys
import random

random.seed(500)

if __name__ == "__main__":
    BSs_input_file = sys.argv[1] 
    BSs_input_file = "../input_scenarios/BSs/{}_BSs.json".format(BSs_input_file)
    users_input_file = sys.argv[2]
    n_user = int(users_input_file)
    users_input_file = "../input_scenarios/users/{}_users.json".format(users_input_file)
    MEC_input_file = sys.argv[3]
    MEC_input_file = "../input_scenarios/MEC_servers/{}_MEC_servers.json".format(MEC_input_file)
    
    fps_1 = random.randint(1, 1000)
    fps_2 = random.randint(1, 1000)
    fps_3 = random.randint(1, 1000)
    fps_4 = random.randint(1, 1000)
    fps_5 = random.randint(1, 1000)
    fps_6 = random.randint(1, 1000)
    fg_1 = fg_2 = fg_3 = fg_4 = fg_5 = fg_6 = random.randint(1, 1000)
    sp_1 = random.randint(1, 1000)
    sp_2 = random.randint(1, 1000)
    sp_3 = random.randint(1, 1000)
    sp_4 = random.randint(1, 1000)

    image_ID = [fps_1, fps_2, fps_3, fps_4, fps_5, fps_6, fg_1, fg_2, fg_3, fg_4, fg_5, fg_6, sp_1, sp_2, sp_3, sp_4]

    BSs = read_BSs(BSs_input_file)
    users = read_users(users_input_file)
    MEC_servers = read_MEC(MEC_input_file)

    solution = run_model(BSs, users, MEC_servers, image_ID)
