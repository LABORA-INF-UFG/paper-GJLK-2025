from docplex.cp.model import CpoModel
from docplex.cp.parameters import CpoParameters
from math import log
from classes import Object
import time
import json
import random
import math

random.seed(6810)

def defineConstants(users, BSs):
    light_speed_air = 0.333 # MILISECONDS

    bit_per_pixel_compression = 0.25 # REF: https://arxiv.org/pdf/2408.12691

    pixel_scale = {2: 2560*1440/230400, 4: 3840*2160/230400, 8: 7680*4320/230400, 12: 11520*6480/230400, 24: 23040*12960/230400}

    processing_latency = max([1024 for user in users])/(10**9) # 1024 bits is the packet size (10 Gbps)

    propagation_latency = 0 # max([bs.range for bs in BSs]) * light_speed_air

    queueing_latency = 0.0001 # sec

    flops_per_pixel = 440 # REF https://openaccess.thecvf.com/content/CVPR2023W/NTIRE/papers/Zamfir_Towards_Real-Time_4K_Image_Super-Resolution_CVPRW_2023_paper.pdf

    resolution_vector = [2, 4, 8, 12, 24]

    return processing_latency, propagation_latency, queueing_latency, bit_per_pixel_compression, pixel_scale, flops_per_pixel, resolution_vector


def imageObjectList(image_ID):
    # THE LABELS FILE HAS THE RESOLUTION 640 X 360 (WIDTH X HEIGHT) WITH 230400 PIXELS
    segmentation_file = open("../input_scenarios/Labels/{}.txt".format(image_ID), "r")
    objects_list = []
    objects_IDs = []
    for line in segmentation_file:
        for num in line.split():
             if num.isdigit() and int(num) not in objects_IDs:
                objects_IDs.append(int(num))
    segmentation_file.close()
    
    for object_ID in objects_IDs:
        segmentation_file = open("../input_scenarios/Labels/{}.txt".format(image_ID), "r")
        num_occurrences = 0
        for line in segmentation_file:
            for num in line.split():
                if num.isdigit() and int(num) == object_ID:
                    num_occurrences += 1
        objects_list.append(Object(object_ID, num_occurrences))
        segmentation_file.close()

    return objects_list


def run_heuristic(BSs, users, MEC_servers, image_ID):
    processing_latency, propagation_latency, queueing_latency, bit_per_pixel_compression, pixel_scale, flops_per_pixel, resolution_vector = defineConstants(users, BSs)

    objects = {}

    for user in users:
        objects[user.ID] = imageObjectList(image_ID[user.ID])

    users_attention = {}
    for user in users:
        users_attention[user.ID] = user.object_attention
    
    for user in users:
        for obj in objects[user.ID]:
            if obj.ID not in users_attention[user.ID]:
                users_attention[user.ID][obj.ID] = 0

    start_time = time.time()

    user_aux = users.copy()
    
    BS_admitted_users = {} # dict with users associated to each BS

    BS_available_BW = {}

    user_served_BW = {}

    user_resolution = {}

    for user in users:
        user_resolution[user.ID] = {}
        for obj in objects[user.ID]:
            user_resolution[user.ID][obj.ID] = 2

    user_FPS = {}

    user_served_MEC = {}

    MEC_available_GPU = {}

    user_MEC_admission = {}

    objects_attention_users = {}

    objects_length_users = {}

    for user in users:
        objects_length_users[user.ID] = {}
        for obj in objects[user.ID]:
            objects_length_users[user.ID][obj.ID] = obj.length
    
    objects_attention_users = {}
    
    for user in users:
        objects_attention_users[user.ID] = []
        for attention in [5, 4, 3, 2, 1, 0]:
            for object in objects[user.ID]:
                if users_attention[user.ID][object.ID] == attention:
                    objects_attention_users[user.ID].append(object)        

    for mec in MEC_servers:
        MEC_available_GPU[mec.ID] = mec.GFLOPs * 10 ** 9

    for bs in BSs:
        BS_admitted_users[bs.ID] = []
        BS_available_BW[bs.ID] = bs.BW
    
    user_BS_admission = {} # dict with the best BS for each user

    bs_ID = -1

    while len(user_aux) > 0: # ENSURE THAT ALL USERS WILL BE ATTENDED BY AT LEAST THE MINIMUM QoE (2K RESOLUTION 30 FPS)
        if bs_ID == 3:
            bs_ID = -1
        
        bs_ID += 1
        user = -1
        user_SINR = -1

        if len(user_aux) == 1:
            bs_ID = 2

        for u in user_aux:
            if u.my_SINR(bs_ID) > user_SINR:
                user = u
                user_SINR = u.my_SINR(bs_ID)
        best_BS = bs_ID

        user_obj_length = 0

        for obj in objects[user.ID]:
            user_obj_length += obj.length

        if best_BS in [0, 2]:
            best_MEC = MEC_servers[0]
        else:
            best_MEC = MEC_servers[1]
        
        user_load = user_obj_length * pixel_scale[2] * bit_per_pixel_compression # load to guarantee the minimum QoE (2K)

        user_BW_demand_1 = user_load/(math.log(1 + (10**(user.my_SINR(best_BS)/10)), 2) * 4)
        
        user_BW_demand_2 = user_load/((1/30) - (best_MEC.latency["BS_{}".format(best_BS)] + propagation_latency + processing_latency + queueing_latency))

        user_BW_demand = max([user_BW_demand_1, user_BW_demand_2])
        
        if BS_available_BW[best_BS] - user_BW_demand < 0 or MEC_available_GPU[best_MEC.ID] - user_obj_length * pixel_scale[2] * 30 * flops_per_pixel < 0:
            continue
        else:
            user_FPS[user.ID] = 30
            BS_admitted_users[best_BS].append(user.ID)
            BS_available_BW[best_BS] -= user_BW_demand
            user_BS_admission[user.ID] = best_BS
            user_served_BW[user.ID] = user_BW_demand
            user_served_MEC[user.ID] = user_obj_length * pixel_scale[2] * 30 * flops_per_pixel
            MEC_available_GPU[best_MEC.ID] -= user_obj_length * pixel_scale[2] * 30 * flops_per_pixel
            user_MEC_admission[user.ID] = best_MEC.ID
            user_aux.remove(user)
    
    for attention in [5, 4, 3, 2, 1, 0]:
        for user in users: # CHANGE THE RESOLUTION FROM 2K TO 4K FOR USERS THAT CAN BE ADMITTED IN 4K
            for obj in objects_attention_users[user.ID]:
                if users_attention[user.ID][obj.ID] == attention:
                    new_user_load = (sum([o.length * pixel_scale[user_resolution[user.ID][o.ID]] for o in objects_attention_users[user.ID] if o.ID != obj.ID]) + objects_length_users[user.ID][obj.ID] * pixel_scale[4]) * bit_per_pixel_compression # load to guarantee the QoE (4K)
                    new_user_BW_demand_1 = new_user_load/(math.log(1 + (10**(user.my_SINR(best_BS)/10)), 2) * 4)
                    new_user_BW_demand_2 = new_user_load/((1/user_FPS[user.ID]) - (best_MEC.latency["BS_{}".format(best_BS)] + propagation_latency + processing_latency + queueing_latency))

                    new_user_BW_demand = max([new_user_BW_demand_1, new_user_BW_demand_2])
                    
                    new_MEC_load = (sum([o.length * pixel_scale[user_resolution[user.ID][o.ID]] for o in objects_attention_users[user.ID] if o.ID != obj.ID]) + objects_length_users[user.ID][obj.ID] * pixel_scale[4]) * user_FPS[user.ID] * flops_per_pixel

                    if BS_available_BW[user_BS_admission[user.ID]] + user_served_BW[user.ID] - new_user_BW_demand < 0 or MEC_available_GPU[user_MEC_admission[user.ID]] + user_served_MEC[user.ID] - new_MEC_load < 0:
                        continue
                    else:
                        user_resolution[user.ID][obj.ID] = 4
                        BS_available_BW[user_BS_admission[user.ID]] -= (new_user_BW_demand - user_served_BW[user.ID])
                        user_served_BW[user.ID] = new_user_BW_demand
                        user_served_MEC[user.ID] = new_MEC_load
                        MEC_available_GPU[user_MEC_admission[user.ID]] -= (new_MEC_load - user_served_MEC[user.ID])
        
        for user in users: # CHANGE THE RESOLUTION FROM 4K TO 8K FOR USERS THAT CAN BE ADMITTED IN 8K
            for obj in objects_attention_users[user.ID]:
                if users_attention[user.ID][obj.ID] == attention and user.device["resolution"] in ["4k", "8k"]:
                    new_user_load = (sum([o.length * pixel_scale[user_resolution[user.ID][o.ID]] for o in objects_attention_users[user.ID] if o.ID != obj.ID]) + objects_length_users[user.ID][obj.ID] * pixel_scale[8]) * bit_per_pixel_compression # load to guarantee the QoE (4K)
                    new_user_BW_demand_1 = new_user_load/(math.log(1 + (10**(user.my_SINR(best_BS)/10)), 2) * 4)
                    new_user_BW_demand_2 = new_user_load/((1/user_FPS[user.ID]) - (best_MEC.latency["BS_{}".format(best_BS)] + propagation_latency + processing_latency + queueing_latency))

                    new_user_BW_demand = max([new_user_BW_demand_1, new_user_BW_demand_2])
                    
                    new_MEC_load = (sum([o.length * pixel_scale[user_resolution[user.ID][o.ID]] for o in objects_attention_users[user.ID] if o.ID != obj.ID]) + objects_length_users[user.ID][obj.ID] * pixel_scale[8]) * user_FPS[user.ID] * flops_per_pixel

                    if BS_available_BW[user_BS_admission[user.ID]] + user_served_BW[user.ID] - new_user_BW_demand < 0 or MEC_available_GPU[user_MEC_admission[user.ID]] + user_served_MEC[user.ID] - new_MEC_load < 0:
                        continue
                    else:
                        user_resolution[user.ID][obj.ID] = 8
                        BS_available_BW[user_BS_admission[user.ID]] -= (new_user_BW_demand - user_served_BW[user.ID])
                        user_served_BW[user.ID] = new_user_BW_demand
                        user_served_MEC[user.ID] = new_MEC_load
                        MEC_available_GPU[user_MEC_admission[user.ID]] -= (new_MEC_load - user_served_MEC[user.ID])
        
        for user in users: # CHANGE THE RESOLUTION FROM 8K TO 12K FOR USERS THAT CAN BE ADMITTED IN 12K
            for obj in objects_attention_users[user.ID]:
                if users_attention[user.ID][obj.ID] == attention and user.device["resolution"] == "8k":
                    new_user_load = (sum([o.length * pixel_scale[user_resolution[user.ID][o.ID]] for o in objects_attention_users[user.ID] if o.ID != obj.ID]) + objects_length_users[user.ID][obj.ID] * pixel_scale[12]) * bit_per_pixel_compression # load to guarantee the QoE (4K)
                    new_user_BW_demand_1 = new_user_load/(math.log(1 + (10**(user.my_SINR(best_BS)/10)), 2) * 4)
                    new_user_BW_demand_2 = new_user_load/((1/user_FPS[user.ID]) - (best_MEC.latency["BS_{}".format(best_BS)] + propagation_latency + processing_latency + queueing_latency))

                    new_user_BW_demand = max([new_user_BW_demand_1, new_user_BW_demand_2])
                    
                    new_MEC_load = (sum([o.length * pixel_scale[user_resolution[user.ID][o.ID]] for o in objects_attention_users[user.ID] if o.ID != obj.ID]) + objects_length_users[user.ID][obj.ID] * pixel_scale[12]) * user_FPS[user.ID] * flops_per_pixel

                    if BS_available_BW[user_BS_admission[user.ID]] + user_served_BW[user.ID] - new_user_BW_demand < 0 or MEC_available_GPU[user_MEC_admission[user.ID]] + user_served_MEC[user.ID] - new_MEC_load < 0:
                        continue
                    else:
                        user_resolution[user.ID][obj.ID] = 12
                        BS_available_BW[user_BS_admission[user.ID]] -= (new_user_BW_demand - user_served_BW[user.ID])
                        user_served_BW[user.ID] = new_user_BW_demand
                        user_served_MEC[user.ID] = new_MEC_load
                        MEC_available_GPU[user_MEC_admission[user.ID]] -= (new_MEC_load - user_served_MEC[user.ID])
        
        for user in users: # CHANGE THE RESOLUTION FROM 12K TO 24K FOR USERS THAT CAN BE ADMITTED IN 24K
            for obj in objects_attention_users[user.ID]:
                if users_attention[user.ID][obj.ID] == attention and user.device["resolution"] == "8k":
                    new_user_load = (sum([o.length * pixel_scale[user_resolution[user.ID][o.ID]] for o in objects_attention_users[user.ID] if o.ID != obj.ID]) + objects_length_users[user.ID][obj.ID] * pixel_scale[24]) * bit_per_pixel_compression # load to guarantee the QoE (4K)
                    new_user_BW_demand_1 = new_user_load/(math.log(1 + (10**(user.my_SINR(best_BS)/10)), 2) * 4)
                    new_user_BW_demand_2 = new_user_load/((1/user_FPS[user.ID]) - (best_MEC.latency["BS_{}".format(best_BS)] + propagation_latency + processing_latency + queueing_latency))

                    new_user_BW_demand = max([new_user_BW_demand_1, new_user_BW_demand_2])
                    
                    new_MEC_load = (sum([o.length * pixel_scale[user_resolution[user.ID][o.ID]] for o in objects_attention_users[user.ID] if o.ID != obj.ID]) + objects_length_users[user.ID][obj.ID] * pixel_scale[24]) * user_FPS[user.ID] * flops_per_pixel

                    if BS_available_BW[user_BS_admission[user.ID]] + user_served_BW[user.ID] - new_user_BW_demand < 0 or MEC_available_GPU[user_MEC_admission[user.ID]] + user_served_MEC[user.ID] - new_MEC_load < 0:
                        continue
                    else:
                        user_resolution[user.ID][obj.ID] = 24
                        BS_available_BW[user_BS_admission[user.ID]] -= (new_user_BW_demand - user_served_BW[user.ID])
                        user_served_BW[user.ID] = new_user_BW_demand
                        user_served_MEC[user.ID] = new_MEC_load
                        MEC_available_GPU[user_MEC_admission[user.ID]] -= (new_MEC_load - user_served_MEC[user.ID])
    
    for user in users: # CHANGE THE FPS FROM 30 TO 60 FOR USERS THAT CAN BE ADMITTED IN 60 FPS
        if user.device["fps"] in [60, 90]:
            new_user_load = sum([o.length * pixel_scale[user_resolution[user.ID][o.ID]] for o in objects_attention_users[user.ID]]) * bit_per_pixel_compression
            new_user_BW_demand_1 = new_user_load/(math.log(1 + (10**(user.my_SINR(best_BS)/10)), 2) * 4)
            new_user_BW_demand_2 = new_user_load/((1/60) - (best_MEC.latency["BS_{}".format(best_BS)] + propagation_latency + processing_latency + queueing_latency))

            new_user_BW_demand = max([new_user_BW_demand_1, new_user_BW_demand_2])
            
            new_MEC_load = sum([o.length * pixel_scale[user_resolution[user.ID][o.ID]] for o in objects_attention_users[user.ID]]) * 60 * flops_per_pixel

            if BS_available_BW[user_BS_admission[user.ID]] + user_served_BW[user.ID] - new_user_BW_demand < 0 or MEC_available_GPU[user_MEC_admission[user.ID]] + user_served_MEC[user.ID] - new_MEC_load < 0:
                continue
            else:
                user_FPS[user.ID] = 60
                BS_available_BW[user_BS_admission[user.ID]] -= (new_user_BW_demand - user_served_BW[user.ID])
                user_served_BW[user.ID] = new_user_BW_demand
                user_served_MEC[user.ID] = new_MEC_load
                MEC_available_GPU[user_MEC_admission[user.ID]] -= (new_MEC_load - user_served_MEC[user.ID])
    
    print(user_resolution)
    print(user_FPS)
    print(BS_available_BW)
    print(MEC_available_GPU)
    print(BS_admitted_users)

    heuristic_QoE = 0

    for user in users:
        heuristic_QoE += log(user_FPS[user.ID]/30) + sum([log(user_resolution[user.ID][obj.ID]/2) * users_attention[user.ID][obj.ID] for obj in objects[user.ID]])
    
    users_QoE = {}
    for user in users:
        users_QoE["User_{}".format(user.ID)] = log(user_FPS[user.ID]/30) + sum([log(user_resolution[user.ID][obj.ID]/2) * users_attention[user.ID][obj.ID] for obj in objects[user.ID]])

    print(heuristic_QoE)

    end_time = time.time()
    
    optimal_value = heuristic_QoE
    print("Solution status: " + "Approximated by heuristic")
    solution_json = {"Instance": {"number_of_users": len(users), "number_of_BSs": len(BSs), "number_of_MECs": len(MEC_servers), "image_ID": image_ID}}
    solution_json["Solution"] = {}
    solution_json["Solution"]["Status"] = "Approximated by heuristic"
    
    print("-------------------------------------------------------------")

    user_SINR = {}

    for user in users:
        user_SINR[user.ID] = {}
        for bs in BSs:
            user_SINR[user.ID][bs.ID] = user.my_SINR(bs.ID)

    solution_json["Solution"]["BS_user_association"] = []
    
    user_vazao = {}
    BS_usage = {}
    user_fps = user_FPS

    for bs in BSs:
        BS_usage[bs.ID] = bs.BW - BS_available_BW[bs.ID]
    
    for user in users:
        user_vazao[user.ID] = user_served_BW[user.ID] * 4 * log(1 + (10**(user_SINR[user.ID][user_BS_admission[user.ID]]/10)), 2)

    solution_json["Solution"]["Object_resolution"] = {}

    user_total_load = {}

    for user in users:
        solution_json["Solution"]["Object_resolution"]["User_{}".format(user.ID)] = []
        for obj in objects[user.ID]:
            solution_json["Solution"]["Object_resolution"]["User_{}".format(user.ID)].append({"Object_ID": obj.ID, "Resolution": user_resolution[user.ID], "Length": obj.length, "Attention": users_attention[user.ID][obj.ID]})

        user_total_load["User_{}".format(user.ID)] = sum([o.length * pixel_scale[user_resolution[user.ID][o.ID]] for o in objects_attention_users[user.ID]]) * bit_per_pixel_compression
        
        solution_json["Solution"]["BS_user_association"].append({"User_{}".format(user.ID): "BS_{}".format(user_BS_admission[user.ID]),
                                                                 "Bandwidth": user_served_BW[user.ID],
                                                                 "SINR": user.my_SINR(user_BS_admission[user.ID]),
                                                                 "Throughput": user_served_BW[user.ID] * 4 * log(1 + (10**(user_SINR[user.ID][user_BS_admission[user.ID]]/10)), 2),
                                                                 "Latency": (user_total_load["User_{}".format(user.ID)]/user_vazao[user.ID]) + propagation_latency + processing_latency + queueing_latency,
                                                                 "FPS": user_fps[user.ID]})

    solution_json["Solution"]["BSs_usage"] = {}

    for bs in BSs:
        solution_json["Solution"]["BSs_usage"]["BS_{}".format(bs.ID)] = BS_usage[bs.ID]
    
    print("-------------------------------------------------------------")

    solution_json["Solution"]["Apps_placement"] = []

    for user in users:
        solution_json["Solution"]["Apps_placement"].append({"User_{}".format(user.ID): "MEC_{}".format(user_MEC_admission[user.ID])})

    solution_json["Solution"]["MEC_usage"] = {}
    
    for mec in MEC_servers:
        solution_json["Solution"]["MEC_usage"]["MEC_{}".format(mec.ID)] = (mec.GFLOPs * 10 ** 9) - MEC_available_GPU[mec.ID]
    
    print("-------------------------------------------------------------")

    user_qoe = []

    for user in users:
        user_qoe.append(0)
    
    for user in users:
        for obj in objects[user.ID]:
            user_qoe[user.ID] += log(user_resolution[user.ID][obj.ID]/2) * users_attention[user.ID][obj.ID]
        user_qoe[user.ID] += log(user_fps[user.ID]/30)
    
    solution_json["Solution"]["Users_QoE"] = users_QoE

    solution_json["Solution"]["Total_QoE"] = optimal_value

    solution_json["Solution"]["Time"] = end_time - start_time

    json.dump(solution_json, open("../optimization_model/solutions/Heuristic_{}_users_{}_BSs_{}_MEC_solution.json".format(len(users), len(BSs), len(MEC_servers)), "w"), indent=4)

    print("-------------------------------------------------------------")
    print("TOTAL TIME: {}".format(end_time - start_time))