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
    
    if n_user == 1:
        sp_1 = random.randint(1, 1000)
        image_ID = [sp_1]

    if n_user == 2:
        fps_1 = random.randint(1, 1000)
        fps_2 = random.randint(1, 1000)
        image_ID = [fps_1, fps_2]
    
    elif n_user == 3:
        fps_1 = random.randint(1, 1000)
        fps_2 = random.randint(1, 1000)
        sp_1 = random.randint(1, 1000)
        image_ID = [fps_1, fps_2, sp_1]
    
    elif n_user == 4:
        fps_1 = random.randint(1, 1000)
        fps_2 = random.randint(1, 1000)
        fg_1 = fg_2 = random.randint(1, 1000)
        image_ID = [fps_1, fps_2, fg_1, fg_2]
    
    elif n_user == 5:
        fps_1 = random.randint(1, 1000)
        fps_2 = random.randint(1, 1000)
        fg_1 = fg_2 = random.randint(1, 1000)
        sp_1 = random.randint(1, 1000)
        image_ID = [fps_1, fps_2, fg_1, fg_2, sp_1]
    
    elif n_user == 6:
        fps_1 = random.randint(1, 1000)
        fps_2 = random.randint(1, 1000)
        fg_1 = fg_2 = random.randint(1, 1000)
        sp_1 = random.randint(1, 1000)
        sp_2 = random.randint(1, 1000)
        image_ID = [fps_1, fps_2, fg_1, fg_2, sp_1, sp_2]
    
    elif n_user == 7:
        fps_1 = random.randint(1, 1000)
        fps_2 = random.randint(1, 1000)
        fg_1 = fg_2 = random.randint(1, 1000)
        sp_1 = random.randint(1, 1000)
        sp_2 = random.randint(1, 1000)
        sp_3 = random.randint(1, 1000)
        image_ID = [fps_1, fps_2, fg_1, fg_2, sp_1, sp_2, sp_3]
    
    elif n_user == 8:
        fps_1 = random.randint(1, 1000)
        fps_2 = random.randint(1, 1000)
        fps_3 = random.randint(1, 1000)
        fg_1 = fg_2 = random.randint(1, 1000)
        sp_1 = random.randint(1, 1000)
        sp_2 = random.randint(1, 1000)
        sp_3 = random.randint(1, 1000)
        image_ID = [fps_1, fps_2, fps_3, fg_1, fg_2, sp_1, sp_2, sp_3]
    
    elif n_user == 9:
        fps_1 = random.randint(1, 1000)
        fps_2 = random.randint(1, 1000)
        fps_3 = random.randint(1, 1000)
        fps_4 = random.randint(1, 1000)
        fg_1 = fg_2 = random.randint(1, 1000)
        sp_1 = random.randint(1, 1000)
        sp_2 = random.randint(1, 1000)
        sp_3 = random.randint(1, 1000)
        image_ID = [fps_1, fps_2, fps_3, fps_4, fg_1, fg_2, sp_1, sp_2, sp_3]
    
    elif n_user == 10:
        fps_1 = random.randint(1, 1000)
        fps_2 = random.randint(1, 1000)
        fps_3 = random.randint(1, 1000)
        fps_4 = random.randint(1, 1000)
        fg_1 = fg_2 = fg_3 = random.randint(1, 1000)
        sp_1 = random.randint(1, 1000)
        sp_2 = random.randint(1, 1000)
        sp_3 = random.randint(1, 1000)
        image_ID = [fps_1, fps_2, fps_3, fps_4, fg_1, fg_2, fg_3, sp_1, sp_2, sp_3]
    
    elif n_user == 11:
        fps_1 = random.randint(1, 1000)
        fps_2 = random.randint(1, 1000)
        fps_3 = random.randint(1, 1000)
        fps_4 = random.randint(1, 1000)
        fg_1 = fg_2 = fg_3 = fg_4 = random.randint(1, 1000)
        sp_1 = random.randint(1, 1000)
        sp_2 = random.randint(1, 1000)
        sp_3 = random.randint(1, 1000)
        image_ID = [fps_1, fps_2, fps_3, fps_4, fg_1, fg_2, fg_3, fg_4, sp_1, sp_2, sp_3]
    
    elif n_user == 12:
        fps_1 = random.randint(1, 1000)
        fps_2 = random.randint(1, 1000)
        fps_3 = random.randint(1, 1000)
        fps_4 = random.randint(1, 1000)
        fps_5 = random.randint(1, 1000)
        fg_1 = fg_2 = fg_3 = fg_4 = random.randint(1, 1000)
        sp_1 = random.randint(1, 1000)
        sp_2 = random.randint(1, 1000)
        sp_3 = random.randint(1, 1000)
        image_ID = [fps_1, fps_2, fps_3, fps_4, fps_5, fg_1, fg_2, fg_3, fg_4, sp_1, sp_2, sp_3]
    
    elif n_user == 13:
        fps_1 = random.randint(1, 1000)
        fps_2 = random.randint(1, 1000)
        fps_3 = random.randint(1, 1000)
        fps_4 = random.randint(1, 1000)
        fps_5 = random.randint(1, 1000)
        fps_6 = random.randint(1, 1000)
        fg_1 = fg_2 = fg_3 = fg_4 = random.randint(1, 1000)
        sp_1 = random.randint(1, 1000)
        sp_2 = random.randint(1, 1000)
        sp_3 = random.randint(1, 1000)
        image_ID = [fps_1, fps_2, fps_3, fps_4, fps_5, fps_6, fg_1, fg_2, fg_3, fg_4, sp_1, sp_2, sp_3]
    
    elif n_user == 14:
        fps_1 = random.randint(1, 1000)
        fps_2 = random.randint(1, 1000)
        fps_3 = random.randint(1, 1000)
        fps_4 = random.randint(1, 1000)
        fps_5 = random.randint(1, 1000)
        fps_6 = random.randint(1, 1000)
        fg_1 = fg_2 = fg_3 = fg_4 = fg_5 = random.randint(1, 1000)
        sp_1 = random.randint(1, 1000)
        sp_2 = random.randint(1, 1000)
        sp_3 = random.randint(1, 1000)
        image_ID = [fps_1, fps_2, fps_3, fps_4, fps_5, fps_6, fg_1, fg_2, fg_3, fg_4, fg_5, sp_1, sp_2, sp_3]
    
    elif n_user == 15:
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
        image_ID = [fps_1, fps_2, fps_3, fps_4, fps_5, fps_6, fg_1, fg_2, fg_3, fg_4, fg_5, fg_6, sp_1, sp_2, sp_3]
    
    elif n_user == 16:
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
