from docplex.cp.model import CpoModel
from docplex.cp.parameters import CpoParameters
from math import log
from classes import Object
import time
import json

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


def run_model(BSs, users, MEC_servers, image_ID):
    model = CpoModel()
    myparams = CpoParameters(LogPeriod=9999999999, SearchType="IterativeDiving", TimeLimit=60*60)
    model.set_parameters(myparams)

    processing_latency, propagation_latency, queueing_latency, bit_per_pixel_compression, pixel_scale, flops_per_pixel, resolution_vector = defineConstants(users, BSs)

    objects = {}

    for user in users:
        objects[user.ID] = imageObjectList(image_ID[user.ID])

    # 2K RESOLUTION 2560 X 1440
    # 4K RESOLUTION 3840 X 2160
    # 8K RESOLUTION 7680 X 4320
    # 12K RESOLUTION 11520 X 6480
    # 24K RESOLUTION 23040 X 12960

    i_resolution_user_object = [] # iterador entre USUARIOS e RESOLUÇÕES
    
    for user in users:
        for object in objects[user.ID]:
                # i_resolution_user_object.append((user.ID, object.ID, 2))    
                i_resolution_user_object.append((user.ID, object.ID, 4))
    
    i_FPS_user = [] # iterador entre USUARIOS e FPS

    for user in users:
        i_FPS_user.append((user.ID, 30))
    
    i_BS_user = [(bs.ID, user.ID) for bs in BSs for user in users] # iterador entre BS e USUARIOS
    i_MEC_user = [(mec.ID, user.ID) for mec in MEC_servers for user in users] # iterador entre MEC e USUARIOS

    model.x_user = model.integer_var_dict(keys=i_BS_user, name="x_user") # variáveis quantidade de banda alocada da BS para USUARIOS
    
    model.y_user = model.binary_var_dict(keys=i_BS_user, name="y_user") # variáveis se USUARIO I é admitido na BS J

    model.w_user_object = model.binary_var_dict(keys=i_resolution_user_object, name="w_user_object") # variáveis se USUARIO I utiliza RESOLUÇÃO J para OBJETO U

    model.u_user = model.binary_var_dict(keys=i_FPS_user, name="u_user") # variáveis quantidade de FPS alocada para USUARIOS

    model.z_user = model.binary_var_dict(keys=i_MEC_user, name="z_user") # variáveis se aplicação do USUARIO I é executado no MEC J

    users_attention = {}
    for user in users:
        users_attention[user.ID] = user.object_attention
    
    for user in users:
        for obj in objects[user.ID]:
            if obj.ID not in users_attention[user.ID]:
                print(user.ID, "do not see", obj.ID)
                users_attention[user.ID][obj.ID] = 0

    # função objetivo
    # model.maximize(model.sum(model.w_user_object[i] * model.sum(model.u_user[(i[0], fps)] * log((i[2] * fps)/2) for fps in [30, 60, 90] if (i[0], fps) in i_FPS_user) * users_attention[i[0]][i[1]] for i in i_resolution_user_object))
    model.maximize(model.sum(model.sum(model.u_user[i] * log(i[1]/30) for i in i_FPS_user if i[0] == user.ID) + 
                             model.sum(model.w_user_object[i] * (log(i[2]/2)) * users_attention[i[0]][i[1]] for i in i_resolution_user_object if i[0] == user.ID) for user in users))

    # restrição para selecionar apenas uma resolução para cada objeto na imagem de cada usuário 
    for user in users:
        for object in objects[user.ID]:
            model.add_constraint(model.sum(model.w_user_object[i] for i in i_resolution_user_object if i[1] == object.ID and i[0] == user.ID) == 1)
    
    # restrição para selecionar apenas uma taxa de FPS para cada usuário 
    for user in users:
        model.add_constraint(model.sum(model.u_user[i] for i in i_FPS_user if i[0] == user.ID) == 1)

    # restrição para posicionar aplicações baseado no conjunto de usuários que a acessa 
    for user_1 in users:
        for user_2 in users:
            model.add_constraint(model.z_user[mec.ID, user_1.ID] == model.z_user[mec.ID, user_2.ID] for mec in MEC_servers 
                                 if user_1.application_ID == user_2.application_ID)
    
    # restrição para posicionar aplicações dos usuários 
    for user in users:
        model.add_constraint(model.sum(model.z_user[mec.ID, user.ID] for mec in MEC_servers) == 1)
    
    # restrição para não permitir que a banda alocada em uma BS seja maior que a capacidade da BS 
    for bs in BSs:
        model.add(model.sum(model.x_user[(bs.ID, user.ID)] for user in users) <= bs.BW)
        for user in users:
            model.add(model.x_user[(bs.ID, user.ID)] >= 0)

    # restricoes para relacionar variaveis, se USUARIO I é admitido na BS J, entao a banda alocada deve ser > 0 
    for bs in BSs:
        for user in users:
            model.add_constraint(model.y_user[bs.ID, user.ID] * bs.BW >= model.x_user[bs.ID, user.ID])
            model.add_constraint(model.y_user[bs.ID, user.ID] <= model.x_user[bs.ID, user.ID])
    
    # todo USUARIO deve ser admitido 
    for user in users:
        model.add_constraint(model.sum(model.y_user[bs.ID, user.ID] for bs in BSs) == 1)

    # A capacidade de renderização do servidor MEC deve ser respeitada 
    for mec in MEC_servers:
        model.add_constraint(model.sum(model.z_user[mec.ID, user.ID] * model.sum(model.sum(model.w_user_object[user.ID, obj.ID, res] * pixel_scale[res] * obj.length for res in resolution_vector if (user.ID, obj.ID, res) in i_resolution_user_object) for obj in objects[user.ID])
                                        * flops_per_pixel * model.sum(model.u_user[user.ID, fps] * fps for fps in [30, 60, 90] if (user.ID, fps) in i_FPS_user) for user in users) <= mec.GFLOPs * 10 ** 9)

    # A banda alocada deve suprir a demanda dos usuários 
    for user in users:
        model.add_constraint(model.sum(model.x_user[bs.ID, user.ID] * 4 * log(1 + (10**(user.my_SINR(bs.ID)/10)), 2) for bs in BSs) 
                             >= model.sum(model.sum(model.w_user_object[user.ID, obj.ID, res] * obj.length * pixel_scale[res] * bit_per_pixel_compression for res in resolution_vector if (user.ID, obj.ID, res) in i_resolution_user_object) for obj in objects[user.ID]))

    # Latency constraint of users in ms 
    for user in users:
        model.add_constraint(model.sum(model.sum(model.w_user_object[user.ID, obj.ID, res] * obj.length * pixel_scale[res] * bit_per_pixel_compression for res in resolution_vector if (user.ID, obj.ID, res) in i_resolution_user_object) for obj in objects[user.ID]) + 
                            (model.sum(model.x_user[bs.ID, user.ID] * 4 * log(1 + (10**(user.my_SINR(bs.ID)/10)), 2)for bs in BSs) * 
                             model.sum(model.z_user[mec.ID, user.ID] * model.sum(model.x_user[bs.ID, user.ID] * mec.latency["BS_{}".format(bs.ID)] for bs in BSs) for mec in MEC_servers)) 
                            <= (model.sum(model.x_user[bs.ID, user.ID] * 4 * log(1 + (10**(user.my_SINR(bs.ID)/10)), 2)for bs in BSs)) * 
                            (model.sum(model.u_user[user.ID, fps] * 1/fps for fps in [30, 60, 90] if (user.ID, fps) in i_FPS_user) - (propagation_latency + processing_latency + queueing_latency)))
    
    start_time = time.time()
    msol = model.solve(agent='local', execfile='/opt/ibm/ILOG/CPLEX_Studio2211/cpoptimizer/bin/x86-64_linux/cpoptimizer')
    end_time = time.time()
    print("\n\n-------------------------- MY LOGS --------------------------")

    if msol:
        optimal_value = msol.get_objective_values()[0]
        print("Solution status: " + msol.get_solve_status())
        solution_json = {"Instance": {"number_of_users": len(users), "number_of_BSs": len(BSs), "number_of_MECs": len(MEC_servers), "image_ID": image_ID}}
        solution_json["Solution"] = {}
        solution_json["Solution"]["Status"] = msol.get_solve_status()
    else:
        print("No feasible solution found!")
        return 0
    
    print("-------------------------------------------------------------")

    user_SINR = {}

    for user in users:
        user_SINR[user.ID] = {}
        for bs in BSs:
            user_SINR[user.ID][bs.ID] = user.my_SINR(bs.ID)

    solution_json["Solution"]["BS_user_association"] = []
    
    user_vazao = {}
    BS_usage = {}
    user_fps = {}

    for i in i_FPS_user:
        if msol[model.u_user[i]] > 0.01:
            user_fps[i[0]] = i[1]

    solution_json["Solution"]["Object_resolution"] = {}

    user_total_load = {}
    for i in i_resolution_user_object:
        if msol[model.w_user_object[i]] > 0.01:
            obj_length = {}
            for obj in objects[i[0]]:
                if obj.ID not in obj_length.keys():
                    obj_length[obj.ID] = obj.length
            if "User_{}".format(i[0]) not in solution_json["Solution"]["Object_resolution"].keys():
                user_total_load["User_{}".format(i[0])] = 0
                solution_json["Solution"]["Object_resolution"]["User_{}".format(i[0])] = []
            solution_json["Solution"]["Object_resolution"]["User_{}".format(i[0])].append({"Object_ID": i[1], "Resolution": i[2], "Length": obj_length[i[1]], "Attention": users_attention[i[0]][i[1]]})
            user_total_load["User_{}".format(i[0])] += obj_length[i[1]] * pixel_scale[i[2]] * bit_per_pixel_compression

    for i in i_BS_user:
        if i[0] not in BS_usage.keys():
                BS_usage[i[0]] = 0
        if msol[model.y_user[i]] > 0.01:
            user_vazao[i[1]] = msol[model.x_user[i]] * 4 * log(1 + (10**(user_SINR[i[1]][i[0]]/10)), 2)
            BS_usage[i[0]] += msol[model.x_user[i]]
            solution_json["Solution"]["BS_user_association"].append({"User_{}".format(i[1]): "BS_{}".format(i[0]), 
                                                                "Bandwidth": msol[model.x_user[i]], 
                                                                "SINR": user_SINR[i[1]][i[0]],
                                                                "Throughput": msol[model.x_user[i]] * 4 * log(1 + (10**(user_SINR[i[1]][i[0]]/10)), 2),
                                                                "Latency": (user_total_load["User_{}".format(i[1])]/user_vazao[i[1]]) + propagation_latency + processing_latency + queueing_latency,
                                                                "FPS": user_fps[i[1]]})
            # print("BS {}: Serving {} MHz for User {}, with {:.1f} Mbps".format(i[0], 
            #                                                      msol[model.x_user[i]],
            #                                                      i[1],
            #                                                      msol[model.x_user[i]] * 4 * log(1 + (10**(user_SINR[i[1]][i[0]]/10)), 2)))

    solution_json["Solution"]["BSs_usage"] = {}

    for bs in BSs:
        solution_json["Solution"]["BSs_usage"]["BS_{}".format(bs.ID)] = BS_usage[bs.ID]
    
    print("-------------------------------------------------------------")

    solution_json["Solution"]["Apps_placement"] = []

    MEC_usage = {}

    for i in i_MEC_user:
        if i[0] not in MEC_usage.keys():
                MEC_usage[i[0]] = 0
        if msol[model.z_user[i]] > 0.01:
            solution_json["Solution"]["Apps_placement"].append({"User_{}".format(i[1]): "MEC_{}".format(i[0])})
            
            for obj in objects[i[1]]:
                for res in [2, 4, 8, 12, 24]: 
                    for fps in [30, 60, 90]:
                        if (i[1], obj.ID, res) in i_resolution_user_object and (i[1], fps) in i_FPS_user:
                            MEC_usage[i[0]] += msol[model.w_user_object[i[1], obj.ID, res]] * pixel_scale[res] * obj.length * flops_per_pixel * msol[model.u_user[i[1], fps]] * fps

            # print("MEC_Server {}: Processing application of User {}".format(i[0], i[1]))
    
    solution_json["Solution"]["MEC_usage"] = {}
    
    for mec in MEC_servers:
        solution_json["Solution"]["MEC_usage"]["MEC_{}".format(mec.ID)] = MEC_usage[mec.ID]
    
    print("-------------------------------------------------------------")

    user_qoe = []

    for user in users:
        user_qoe.append(0)

    solution_json["Solution"]["Object_resolution"] = {}

    for i in i_resolution_user_object:
        if msol[model.w_user_object[i]] > 0.01:
            obj_length = {}
            for obj in objects[i[0]]:
                if obj.ID not in obj_length.keys():
                    obj_length[obj.ID] = obj.length
            if "User_{}".format(i[0]) not in solution_json["Solution"]["Object_resolution"].keys():
                solution_json["Solution"]["Object_resolution"]["User_{}".format(i[0])] = []
            solution_json["Solution"]["Object_resolution"]["User_{}".format(i[0])].append({"Object_ID": i[1], "Resolution": i[2], "Length": obj_length[i[1]], "Attention": users_attention[i[0]][i[1]]})
            # print("User {} is using resolution {} for object {} with length {} and attention {}".format(i[0], i[2], i[1], obj_length[i[1]], users_attention[i[0]][i[1]]))
            
            user_qoe[i[0]] += log(i[2]/2) * users_attention[i[0]][i[1]]

    for i in range(0, len(user_qoe)):
        print(i, user_qoe[i])
        user_qoe[i] += log(user_fps[i]/30)
        print(i, user_qoe[i])

    qoe_sum = 0
    solution_json["Solution"]["Users_QoE"] = {}        
    for user in users:
        solution_json["Solution"]["Users_QoE"]["User_{}".format(user.ID)] = user_qoe[user.ID]
        qoe_sum += user_qoe[user.ID]
    
    solution_json["Solution"]["Total_QoE"] = optimal_value

    solution_json["Solution"]["Time"] = round(end_time - start_time, 2)

    json.dump(solution_json, open("solutions/Only_LQ_{}_users_{}_BSs_{}_MEC_solution.json".format(len(users), len(BSs), len(MEC_servers)), "w"), indent=4)

    print("-------------------------------------------------------------")
    print("TOTAL TIME: {}".format(end_time - start_time))