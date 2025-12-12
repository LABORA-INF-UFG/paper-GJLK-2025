from docplex.mp.model import Model
from docplex.cp.parameters import CpoParameters
from math import log2, log
from methods import read_input_files
from classes import OBJECT
import os
import sys
import json
import time
import random
import pandas as pd

random.seed(42)

def imageObjectList(image_ID):
    json_obj = json.load(open("../input_files/Objects/{}.json".format(image_ID)))
    objects_list = []
    for object in json_obj["objects"]:
        objects_list.append(OBJECT(object["object_ID"], object["length"]))

    return objects_list

def get_users_priority(Users, Games):
    users_priority = {}
    for u in Users:
        if Games[u.my_game() - 1].my_game_type() == "quality":
            users_priority[u.my_ID()] = 1
        else:
            users_priority[u.my_ID()] = 0
    return users_priority

def resolution_pixel_size():
    return {"1080p": 1920 * 1080,
            "2K": 2560 * 1440,
            "4K": 3840 * 2160}


def get_users_game_requirements(Users, Games, sol):
    flops_per_pixel = 440 # REF https://openaccess.thecvf.com/content/CVPR2023W/NTIRE/papers/Zamfir_Towards_Real-Time_4K_Image_Super-Resolution_CVPRW_2023_paper.pdf
    users_CPU_demand = {}
    users_RAM_demand = {}
    users_GPU_demand = {}
    users_total_load = {}
    users_load_to_gNB = {}
    users_latency_to_gNB = {}
    users_frame_rate = {}
    users_resolution = {}
    users_serving_gNBs = {}
    users_throughput = {}
    users_total_PRBs = {}
    users_gNB_PRBs = {}

    for user in Users:
        for g in Games:
            if g.my_ID() == user.my_game():
                game = g
        users_CPU_demand[user.my_ID()] = game.my_CPU_requirement()
        users_RAM_demand[user.my_ID()] = game.my_RAM_requirement()
        for u in sol["solution"]["users"]:
            if u["ID"] == user.my_ID():
                u_resolution = u["resolution"]
                u_frame_rate = u["frame_rate"]
                users_throughput[user.my_ID()] = u["total_throughput"]
                users_total_load[user.my_ID()] = u["total_load"]
                users_frame_rate[user.my_ID()] = u["frame_rate"]
                users_resolution[user.my_ID()] = u["resolution"]
                users_serving_gNBs[user.my_ID()] = u["serving_gNBs"]
                users_total_PRBs[user.my_ID()] = u["Total_PRBs"]
                users_load_to_gNB[user.my_ID()] = {}
                users_latency_to_gNB[user.my_ID()] = {}
                users_gNB_PRBs[user.my_ID()] = {}
                for ggnb in u["serving_gNBs"]:
                    users_gNB_PRBs[user.my_ID()][ggnb] = u["PRBs"][str(ggnb)]
                for gNB in u["load_to_gNB"]:
                    users_load_to_gNB[user.my_ID()][gNB] = u["load_to_gNB"][gNB]
                    users_latency_to_gNB[user.my_ID()][gNB] = u["latency_to_gNB"][gNB]

        if u_resolution == "1080p":
            n_pixels = 1920 * 1080
        elif u_resolution == "2K":
            n_pixels = 2560 * 1440
        elif u_resolution == "4K":
            n_pixels = 3840 * 2160
        users_GPU_demand[user.my_ID()] = n_pixels * flops_per_pixel * u_frame_rate

    return users_CPU_demand, users_RAM_demand, users_GPU_demand, users_total_load, users_load_to_gNB, users_latency_to_gNB, users_frame_rate, users_resolution, users_serving_gNBs, users_throughput, users_total_PRBs, users_gNB_PRBs


def model(n_CNs, n_GNBs, n_users, numerology, timestamp):

    # maximum latency value (delta max)
    delta_max = 1
    
    # read input files
    CNs, GNBs, Games, Users, Paths, Links, Links_latency, Links_bandwidth = read_input_files(n_CNs, n_GNBs, n_users, timestamp)

    # get user's computational requirements based on image quality and throughput
    sol = json.load(open("../solutions/first_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), 'r'))
    users_CPU_demand, users_RAM_demand, users_GPU_demand, users_total_load, users_load_to_gNB, users_latency_to_gNB, users_frame_rate, users_resolution, users_serving_gNBs, users_throughput, users_total_PRBs, users_gNB_PRBs = get_users_game_requirements(Users, Games, sol)

    # considering codec to compress the video stream as 0.25 bit per pixel
    codec_bpp = 0.25 # REF: https://arxiv.org/pdf/2408.12691
    
    users_frames = {}

    for user in Users:
        users_frames[user.my_ID()] = [random.randint(1, 1000) for i in range(users_frame_rate[user.my_ID()])]

    users_objects = {}
    for user in Users:
        users_objects[user.ID] = []
        count = 1
        for image_ID in users_frames[user.my_ID()]:
            count += 1
            users_objects[user.ID].append(imageObjectList(image_ID))

    users_objects_unique = {}
    for user in Users:
        users_objects_unique[user.ID] = []
        for object_list in users_objects[user.ID]:
            for object in object_list:
                if object.ID not in users_objects_unique[user.ID]:
                    users_objects_unique[user.ID].append(object.ID)

    resolution_list = ["1080p", "2K", "4K"]
    resolution_to_integer = {"1080p": 1, "2K": 2, "4K": 3}

    pixel_scale = {"1080p": 1920*1080/230400, "2K": 2560*1440/230400, "4K": 3840*2160/230400}

    TTIs = [i for i in range(0, 2000)]

    number_of_time_blocks = 60
    TTIs_in_time_block = int(len(TTIs)/number_of_time_blocks)

    gNB_objects = {}
    object_ID_to_objects = {}
    
    for user in Users:
        for object_list in users_objects[user.ID]:
            for object in object_list:
                if object.ID not in object_ID_to_objects:
                    object_ID_to_objects[object.ID] = object

    for gNB in GNBs:
        gNB_objects[gNB.my_ID()] = gNB

    # instantiate constraint programming model
    model = Model(name="Third stage", log_output=True)
    model.parameters.mip.tolerances.mipgap = 0.01
    model.parameters.emphasis.mip = 2

    # # define decision variable iterators
    Users_object_resolution_frame = [(user.ID, object.ID, res, frame) for user in Users for frame in range(users_frame_rate[user.ID]) for object in users_objects[user.ID][frame] for res in resolution_list]
    Users_gNB_time = [(u.ID, b, k) for u in Users for b in users_serving_gNBs[u.ID] for k in TTIs]

    # decision variable that indicates if user u see object o with resolution res at time t
    model.w = model.binary_var_dict(Users_object_resolution_frame, name="object_resolution")
    # decision variable that indicates if user u receive data from gNB b at time t
    model.r = model.binary_var_dict(Users_gNB_time, name="user_gNB_transmission")
    # decision variable that indicates the amount of PRBs allocated to user u in gNB b at time t
    model.n = model.integer_var_dict(Users_gNB_time, name="PRBs_allocation")

    users_attention = {}

    for u in Users:
        users_attention[u.my_ID()] = {}
        df = pd.read_csv(open("../input_files/my_rating.csv", "r"))
        for index, row in df.iterrows():
            if row['userId'] == u.my_ID()%160:
                users_attention[u.my_ID()][int(row['objectId'])] = int(row['rating'])

    # objective function - maximize users QoE based on attention following Webber Fachner satisfaction law
    model.maximize(model.sum(model.sum(model.w[i] * log(resolution_to_integer[i[2]]) * (users_attention[u.my_ID()][i[1]] if i[1] in users_attention[u.my_ID()] else 1) for i in Users_object_resolution_frame if i[0] == u.ID) for u in Users))

    # # MTP constraint
    # for u in Users:
    #     for b in users_serving_gNBs[u.my_ID()]:
    #         for k1 in TTIs:
    #             for k2 in TTIs:
    #                 if k1 < k2:
    #                     model.add_constraint(model.r[u.ID, b, k1] * model.r[u.ID, b, k2] + ((k2 - k1) * 0.5) <= 50, "MTP_constraint_User_{}_gNB_{}_TTI_{}_{}".format(u.my_ID(), b, k1, k2))
                

    # each user must receive data from gNB at least at one TTI
    for u in Users:
        for b in users_serving_gNBs[u.ID]:
            model.add_constraint(model.sum(model.r[u.ID, b, k] for k in TTIs) >= 1)
    
    # the gNB number of PRBs must not exceed its capacity in each TTI
    for k in TTIs:
        for b in GNBs:
            model.add_constraint(model.sum(model.n[u.ID, b.my_ID(), k] for u in Users if b.my_ID() in users_serving_gNBs[u.ID]) <= b.my_number_PRBs())

    # if user is receiving data from gNB, then its allocated PRBs must be greater than 0
    for i in Users_gNB_time:
        model.add_constraint(gNB_objects[i[1]].my_number_PRBs() * model.r[i] >= model.n[i])
        model.add_constraint(model.n[i] >= model.r[i])
    
    # each object must have a resolution assigned in each frame
    for user in Users:
        for frame in range(users_frame_rate[user.ID]):
            for object in users_objects[user.ID][frame]:
                model.add_constraint(model.sum(model.w[user.ID, object.ID, res, frame] for res in resolution_list) == 1)
    
    # the transmission load of the objects cannot exceed the throughput for user u
    for user in Users:
        user_objects_load = model.sum(model.w[user.ID, object.ID, res, frame] * pixel_scale[res] * object.length * codec_bpp for frame in range(users_frame_rate[user.ID]) for object in users_objects[user.my_ID()][frame] for res in resolution_list)
        user_throughput = model.sum(model.n[user.ID, b, k] * (gNB_objects[b].my_PRB_BW() * 10 ** 6) * user.my_SE(b) for b in users_serving_gNBs[user.my_ID()] for k in TTIs)
        model.add_constraint(user_objects_load <= user_throughput, "throghput_constraint_User_{}".format(user.my_ID()))
    
    # the number of PRBs allocated to user u in all TTIs must not exceed the number of PRBs allocated in the first stage
    for user in Users:
            model.add_constraint(model.sum(model.n[user.ID, b, k] for k in TTIs for b in users_serving_gNBs[user.my_ID()]) == max(users_total_PRBs[user.my_ID()], number_of_time_blocks), "PRBs_constraint_User_{}_gNB_{}".format(user.my_ID(), b))

    for user in Users:
        for b in users_serving_gNBs[user.my_ID()]:
            time_block = 1
            while time_block * TTIs_in_time_block <= len(TTIs):
                if time_block == number_of_time_blocks:
                    TTIs_block = TTIs[((time_block - 1) * TTIs_in_time_block):]
                else:
                    TTIs_block = TTIs[((time_block - 1) * TTIs_in_time_block):(time_block * TTIs_in_time_block)]
                model.add_constraint(model.sum(model.r[user.ID, b, k] for k in TTIs_block) >= 1, "MTP")
                model.add_constraint(model.sum(model.n[user.ID, b, k] for k in TTIs_block) >= (max(users_gNB_PRBs[user.my_ID()][b], number_of_time_blocks)//number_of_time_blocks), "MTP")
                time_block += 1
    
    for user in Users:
        time_block = 1
        while time_block * TTIs_in_time_block <= len(TTIs):
            if time_block == number_of_time_blocks:
                TTIs_block = TTIs[((time_block - 1) * TTIs_in_time_block):]
            else:
                TTIs_block = TTIs[((time_block - 1) * TTIs_in_time_block):(time_block * TTIs_in_time_block)]
            model.add_constraint(model.sum(model.n[user.ID, b, k] for b in users_serving_gNBs[user.my_ID()] for k in TTIs_block) <= (max(users_total_PRBs[user.my_ID()], number_of_time_blocks)//number_of_time_blocks) + 1, "MTP")
            time_block += 1

    start_time = time.time()
    model.solve()
    elapsed_time = time.time() - start_time

    if model.solution is not None:
        solution_json = {"solution": {"Total_QoE": model.solution.get_objective_value(), "time": elapsed_time, "users": []},}
        for user in Users:
            solution_json["solution"]["users"].append({})
            solution_json["solution"]["users"][user.ID]["objects_resolution_per_frame"] = []
            solution_json["solution"]["users"][user.ID]["received_PRBs_in_TTI_per_gNB"] = []
            solution_json["solution"]["users"][user.ID]["ID"] = user.ID
        for user in Users:
            for frame in range(users_frame_rate[user.ID]):
                solution_json["solution"]["users"][user.ID]["objects_resolution_per_frame"].append({})
                for object in users_objects[user.ID][frame]:
                    for res in resolution_list:
                        if model.w[user.ID, object.ID, res, frame].solution_value == 1:
                            solution_json["solution"]["users"][user.ID]["objects_resolution_per_frame"][frame][object.ID] = res
        
        for user in Users:
            for b in users_serving_gNBs[user.my_ID()]:
                gNB_distributed_PRBs = {}
                for tti in TTIs:
                    if model.n[user.ID, b, tti].solution_value > 0:
                        gNB_distributed_PRBs[tti] = model.n[user.ID, b, tti].solution_value
                solution_json["solution"]["users"][user.ID]["received_PRBs_in_TTI_per_gNB"].append({"gNB": b, "TTIs": gNB_distributed_PRBs})
        
        distributed_PRBs_in_each_time_block = {}
        for user in Users:
            distributed_PRBs_in_each_time_block[user.my_ID()] = [0 for i in range(number_of_time_blocks)]
        for i in Users_gNB_time:
            if model.r[i].solution_value == 1:
                time_block = (i[2] // TTIs_in_time_block)
                if time_block == number_of_time_blocks:
                    time_block = number_of_time_blocks - 1
                distributed_PRBs_in_each_time_block[i[0]][time_block] += model.n[i].solution_value
        for user in Users:
            for i in range(len(distributed_PRBs_in_each_time_block[user.my_ID()])):
                if distributed_PRBs_in_each_time_block[user.my_ID()][i] > 0:
                    print("User {} receives {} PRBs in time block {}".format(user.my_ID(), distributed_PRBs_in_each_time_block[user.my_ID()][i], i))
        for user in Users:
            load = 0
            tp = 0
            for frame in range(users_frame_rate[user.my_ID()]):
                for object in users_objects[user.my_ID()][frame]:
                    for res in resolution_list:
                        load += model.w[user.ID, object.ID, res, frame].solution_value * pixel_scale[res] * object.length * codec_bpp
            for b in users_serving_gNBs[user.my_ID()]:
                for k in TTIs:
                    tp += model.n[user.ID, b, k].solution_value * (gNB_objects[b].my_PRB_BW() * 10 ** 6) * user.my_SE(b)
            if load > 0:
                print("User {} load {}".format(user.my_ID(), load))
            if tp > 0:
                print("User {} throughput {}".format(user.my_ID(), tp))

        # for user in Users:
        #     max_mtp = 0
        #     for b in users_serving_gNBs[user.my_ID()]:
        #         for k1 in TTIs:
        #             for k2 in TTIs:
        #                 if k1 < k2:
        #                     if model.r[user.ID, b, k1].solution_value * model.r[user.ID, b, k2].solution_value == 1:
        #                         mtp = (k2 - k1) * 0.5
        #                         if mtp > max_mtp:
        #                             max_mtp = mtp
        #     print("User {} gNB {} MTP {}".format(user.my_ID(), b, max_mtp))

        json.dump(solution_json, open("../solutions/third_stage/optimal_model/{}_CNs_{}_gNBs_{}_users.json".format(n_CNs, n_GNBs, n_users), 'w'), indent=4)
    else:
        print("No solution found")

if __name__ == "__main__":
    n_CNs = int(sys.argv[1])
    n_GNBs = int(sys.argv[2])
    n_users = int(sys.argv[3])
    numerology = 1
    for timestamp in range(0, 1):
        model(n_CNs, n_GNBs, n_users, numerology, timestamp)