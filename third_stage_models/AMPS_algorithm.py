from math import log
from methods import read_input_files
from classes import OBJECT
import sys
import json
import time
import random
import pandas as pd
from MTPsched import MTPsched

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
    user_throughput_to_gNB = {}
    users_total_PRBs = {}
    users_gNB_PRBs = {}
    users_served_PRBs_gNB = {}

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
                user_throughput_to_gNB[user.my_ID()] = {}
                users_served_PRBs_gNB[user.my_ID()] = {}
                for ggnb in u["serving_gNBs"]:
                    users_gNB_PRBs[user.my_ID()][ggnb] = u["PRBs"][str(ggnb)]
                for gNB in u["load_to_gNB"]:
                    users_load_to_gNB[user.my_ID()][gNB] = u["load_to_gNB"][gNB]
                    users_latency_to_gNB[user.my_ID()][gNB] = u["latency_to_gNB"][gNB]
                    user_throughput_to_gNB[user.my_ID()][gNB] = u["throughput_to_gNB"][gNB]
                    if "gNB_PRBs" in u:
                        users_served_PRBs_gNB[user.my_ID()][gNB] = u["gNB_PRBs"][gNB]
                    else:
                        users_served_PRBs_gNB[user.my_ID()][gNB] = u["gNBs_PRBs"][gNB]

        if u_resolution == "1080p":
            n_pixels = 1920 * 1080
        elif u_resolution == "2K":
            n_pixels = 2560 * 1440
        elif u_resolution == "4K":
            n_pixels = 3840 * 2160
        users_GPU_demand[user.my_ID()] = n_pixels * flops_per_pixel * u_frame_rate

    return users_CPU_demand, users_RAM_demand, users_GPU_demand, users_total_load, users_load_to_gNB, users_latency_to_gNB, users_frame_rate, users_resolution, users_serving_gNBs, users_throughput, users_total_PRBs, users_gNB_PRBs, user_throughput_to_gNB, users_served_PRBs_gNB


def AMPS(n_CNs, n_GNBs, n_users, numerology, timestamp):
    # maximum latency value (delta max)
    delta_max = 1
    
    # read input files
    CNs, GNBs, Games, Users, Paths, Links, Links_latency, Links_bandwidth = read_input_files(n_CNs, n_GNBs, n_users, timestamp)

    # get user's computational requirements based on image quality and throughput
    if n_users <= 200:
        sol = json.load(open("../solutions/first_stage/optimal_model/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), 'r'))
    else:
        sol = json.load(open("../solutions/first_stage/QoE_aware_heuristic/{}_CNs_{}_gNBs_{}_users_timestamp_{}.json".format(n_CNs, n_GNBs, n_users, timestamp), 'r'))
    
    users_CPU_demand, users_RAM_demand, users_GPU_demand, users_total_load, users_load_to_gNB, users_latency_to_gNB, users_frame_rate, users_resolution, users_serving_gNBs, users_throughput, users_total_PRBs, users_gNB_PRBs, user_throughput_to_gNB, users_served_PRBs_gNB = get_users_game_requirements(Users, Games, sol)

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

    number_of_time_blocks = 30
    TTIs_in_time_block = int(len(TTIs)/number_of_time_blocks)

    # gNB_objects = {}
    # object_ID_to_objects = {}
    
    # for user in Users:
    #     for object_list in users_objects[user.ID]:
    #         for object in object_list:
    #             if object.ID not in object_ID_to_objects:
    #                 object_ID_to_objects[object.ID] = object

    # for gNB in GNBs:
    #     gNB_objects[gNB.my_ID()] = gNB

    # users_attention = {}

    # for u in Users:
    #     users_attention[u.my_ID()] = {}
    #     df = pd.read_csv(open("../input_files/my_rating.csv", "r"))
    #     for index, row in df.iterrows():
    #         if row['userId'] == u.my_ID()%160:
    #             users_attention[u.my_ID()][int(row['objectId'])] = int(row['rating'])
    
    # user_object_resolution = {}

    # user_number_of_objects = {}

    # for user in Users:
    #     user_object_resolution[user.ID] = {}
    #     user_number_of_objects[user.ID] = 0
    #     frame = 0
    #     for list_of_objects in users_objects[user.ID]:
    #         user_number_of_objects[user.ID] += len(list_of_objects)
    #         user_object_resolution[user.ID][frame] = {}
    #         for object in list_of_objects:
    #             user_object_resolution[user.ID][frame][object.ID] = users_resolution[user.ID]
    #             if object.ID not in users_attention[user.ID]:
    #                 users_attention[user.ID][object.ID] = 1
    #         frame += 1

    # objects_sorted_by_attention = {}
    # objects_sorted_by_length = {}

    # # sort objects for each user based on attention and length
    # for user in Users:
    #     objects_sorted_by_attention[user.ID] = {}
    #     objects_sorted_by_length[user.ID] = {}
    #     frame = 0
    #     for list_of_obj in users_objects[user.ID]:
    #         objects_sorted_by_attention[user.ID][frame] = sorted(
    #             list_of_obj,
    #             key=lambda x: (users_attention[user.my_ID()].get(x, 0), -x.length),
    #             reverse=True
    #         )
    #         objects_sorted_by_length[user.ID][frame] = sorted(
    #             list_of_obj,
    #             key=lambda x: x.length,
    #             reverse=True
    #         )
    #         frame += 1

    # Users_sorted_by_resolution = sorted(Users, key=lambda x: -resolution_to_integer[x.max_resolution], reverse=True)
    start_time = time.time()
    # for i in range(0, 2):
    #     # For all users, we will try to maximize the objects resolution according to their attention and length
    #     for user in Users_sorted_by_resolution:
    #         for frame in range(len(users_objects[user.ID])):
    #             list_of_obj = objects_sorted_by_attention[user.ID][frame]
    #             for object in list_of_obj:
    #                 obj_current_resolution = user_object_resolution[user.ID][frame][object.ID]

    #                 # selects the new resolution to be assigned based on the current resolution and user's maximum resolution
    #                 if obj_current_resolution == "1080p":
    #                     new_obj_resolution = "2K"
    #                 elif obj_current_resolution:
    #                     new_obj_resolution = "4K"
    #                 else:
    #                     continue
    #                 # calculate the current object total load
    #                 current_object_load = object.length * pixel_scale[obj_current_resolution] * codec_bpp

    #                 # calculate the transmission load of the object with the new resolution
    #                 new_object_load = object.length * pixel_scale[new_obj_resolution] * codec_bpp
    #                 # boolean variable that represents if the new resolution is feasible or not
    #                 feasible = True

    #                 new_gNB_load = {}

    #                 # Check if the new resolution is feasible considering the transmission load and the troughput to each gNB
    #                 for gNB in users_serving_gNBs[user.my_ID()]:
    #                     # caculate the current throughput to gNB
    #                     current_throughput = user_throughput_to_gNB[user.my_ID()][str(gNB)]/users_frame_rate[user.my_ID()]
    #                     # calculate the current load to gNB
    #                     current_load_to_gNB = users_load_to_gNB[user.my_ID()][str(gNB)]/users_frame_rate[user.my_ID()]
    #                     # calculate the load ratio for the user to the gNB
    #                     load_ratio = current_load_to_gNB/users_total_load[user.my_ID()]
                        
    #                     # calculate the new demand throughput to the gNB if the resolution is changed
    #                     new_demand = current_load_to_gNB - (current_object_load * load_ratio) + (new_object_load * load_ratio)
                        
    #                     # check if the new demand is feasible with the current throughput to gNB - if it is not, we will try to change the resolution of other objects with lower attention
    #                     if new_demand > current_throughput:
    #                         feasible = False
    #                         break
    #                     else:
    #                         new_gNB_load[gNB] = users_load_to_gNB[user.my_ID()][str(gNB)] - current_object_load + new_object_load
                    
    #                 if feasible:
    #                     # update object resolution
    #                     user_object_resolution[user.ID][frame][object.ID] = new_obj_resolution
    #                     # update load to gNB
    #                     for gNB in users_serving_gNBs[user.my_ID()]:
    #                         users_load_to_gNB[user.my_ID()][str(gNB)] = new_gNB_load[gNB]
    #                     # update total load
    #                     users_total_load[user.my_ID()] = sum(users_load_to_gNB[user.my_ID()].values())
    #                     continue

    #                 # look for objects with lower attention sorted by length
    #                 list_of_trade_obj = objects_sorted_by_length[user.ID][frame]
    #                 for trade_object in list_of_trade_obj:
    #                     if trade_object.ID == object.ID:
    #                         continue
    #                     # if the object selected has lower attention than the current object, we will try to change its resolution to fit the new resolution for the object with higher attention
    #                     if users_attention[user.ID][trade_object.ID] < users_attention[user.ID][object.ID]:
    #                         # calculate the current resolution of the trade object and the new LOWER resolution to be assigned
    #                         trade_obj_current_resolution = user_object_resolution[user.ID][frame][trade_object.ID]
    #                         if trade_obj_current_resolution == "1080p":
    #                             continue
    #                         elif trade_obj_current_resolution == "2K":
    #                             new_trade_obj_resolution = "1080p"
    #                         elif trade_obj_current_resolution == "4K":
    #                             new_trade_obj_resolution = "2K"

    #                         # calculate the current load of the trade object
    #                         trade_current_load = trade_object.length * pixel_scale[trade_obj_current_resolution] * codec_bpp
    #                         # calculate the new load of the trade object with the new LOWER resolution
    #                         trade_new_load = trade_object.length * pixel_scale[new_trade_obj_resolution] * codec_bpp

    #                         # boolean variable that represents if the new resolution is feasible or not
    #                         feasible = True
                            
    #                         for gNB in users_serving_gNBs[user.my_ID()]:
    #                             # caculate the current throughput to gNB
    #                             current_throughput = user_throughput_to_gNB[user.my_ID()][str(gNB)]/users_frame_rate[user.my_ID()]
    #                             # calculate the current load to gNB
    #                             current_load_to_gNB = users_load_to_gNB[user.my_ID()][str(gNB)]/users_frame_rate[user.my_ID()]
    #                             # calculate the load ratio for the user to the gNB
    #                             load_ratio = current_load_to_gNB/users_total_load[user.my_ID()]
    #                             # calculate the new demand throughput to the gNB if the resolution of the trade object is changed to a LOWER resolution and the current object resolution is changed to a HIGHER resolution
    #                             new_demand = current_load_to_gNB - (current_object_load * load_ratio) - (trade_current_load * load_ratio) + (trade_new_load * load_ratio) + (new_object_load * load_ratio)
    #                             if new_demand > current_throughput:
    #                                 feasible = False
    #                                 break
    #                             else:
    #                                 new_gNB_load[gNB] = users_load_to_gNB[user.my_ID()][str(gNB)] - current_object_load - trade_current_load + trade_new_load + new_object_load
                            
    #                         if feasible:
    #                             # update object resolution
    #                             user_object_resolution[user.ID][frame][object.ID] = new_obj_resolution
    #                             user_object_resolution[user.ID][frame][trade_object.ID] = new_trade_obj_resolution
    #                             # update load to gNB
    #                             for gNB in users_serving_gNBs[user.my_ID()]:
    #                                 users_load_to_gNB[user.my_ID()][str(gNB)] = new_gNB_load[gNB]
    #                             # update total load
    #                             users_total_load[user.my_ID()] = sum(users_load_to_gNB[user.my_ID()].values())
    #                             continue

    # # calculating the QoE of users
    # users_QoE = {}
    # for user in Users:
    #     users_QoE[user.my_ID()] = 0
    #     for frame in range(users_frame_rate[user.ID]):
    #         for object in users_objects[user.ID][frame]:
    #             users_QoE[user.my_ID()] += log(resolution_to_integer[user_object_resolution[user.ID][frame][object.ID]]) * users_attention[user.my_ID()][object.ID]
    
    # total_QoE = sum(users_QoE.values())
    # print("Total QoE: {}".format(total_QoE))
            
    users_offered_PRBs_gNB, users_MTP_latency, gNB_spectrum= MTPsched(GNBs, users_served_PRBs_gNB, TTIs, number_of_time_blocks)

    elapsed_time = time.time() - start_time

    # solution_json = {"solution": {"Total_QoE": total_QoE, "time": elapsed_time, "users": []},}
    # for user in Users:
    #     solution_json["solution"]["users"].append({})
    #     solution_json["solution"]["users"][user.ID]["number_of_objects"] = user_number_of_objects[user.ID]
    #     solution_json["solution"]["users"][user.ID]["MTP_latency"] = users_MTP_latency[user.my_ID()]
    #     solution_json["solution"]["users"][user.ID]["objects_resolution_per_frame"] = []
    #     solution_json["solution"]["users"][user.ID]["received_PRBs_in_TTI_per_gNB"] = []
    #     solution_json["solution"]["users"][user.ID]["ID"] = user.ID
    # for user in Users:
    #     for frame in range(users_frame_rate[user.ID]):
    #         solution_json["solution"]["users"][user.ID]["objects_resolution_per_frame"].append({})
    #         for object in users_objects[user.ID][frame]:
    #             solution_json["solution"]["users"][user.ID]["objects_resolution_per_frame"][frame][object.ID] = user_object_resolution[user.ID][frame][object.ID]

    user_gNB_PRB_and_TTI = {}

    for user in Users:
        user_gNB_PRB_and_TTI[user.my_ID()] = {}
        for gNB in gNB_spectrum:
            for TTI in range(2000):
                if gNB_spectrum[gNB][TTI] and user.my_ID() in gNB_spectrum[gNB][TTI]:
                    if gNB not in user_gNB_PRB_and_TTI[user.my_ID()]:
                        user_gNB_PRB_and_TTI[user.my_ID()][gNB] = []
                    user_gNB_PRB_and_TTI[user.my_ID()][gNB].append(TTI)

    # for user in user_gNB_PRB_and_TTI:
    #     for gNB in user_gNB_PRB_and_TTI[user]:
    #         TTIs_PRB = {}
    #         for TTI in user_gNB_PRB_and_TTI[user][gNB]:
    #             TTIs_PRB[TTI] = 1
    #         solution_json["solution"]["users"][user]["received_PRBs_in_TTI_per_gNB"].append({"gNB": gNB, "TTIs": TTIs_PRB})

    # json.dump(solution_json, open("../solutions/third_stage/AMPS_MTPsched/{}_CNs_{}_gNBs_{}_users.json".format(n_CNs, n_GNBs, n_users), 'w'), indent=4)

if __name__ == "__main__":
    n_CNs = int(sys.argv[1])
    n_GNBs = int(sys.argv[2])
    n_users = int(sys.argv[3])
    numerology = 1
    for timestamp in range(0, 1):
        AMPS(n_CNs, n_GNBs, n_users, numerology, timestamp)