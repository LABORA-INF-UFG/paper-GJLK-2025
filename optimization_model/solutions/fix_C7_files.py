import json
from math import log

user_TP_coeficient = {}

pixel_scale = {2: 2560*1440/230400, 4: 3840*2160/230400, 8: 7680*4320/230400, 12: 11520*6480/230400, 24: 23040*12960/230400}

for n_user in range(2, 11):
    json_obj = json.load(open('C7_{}_users_5_BSs_5_MEC_solution.json'.format(n_user), 'r'))
    # for user in json_obj["Solution"]["Users_QoE"]:
    #     json_obj["Solution"]["Users_QoE"][user]
    for user in json_obj["Solution"]["Users_Render_QoE"]:
        print(json_obj["Solution"]["Users_Render_QoE"][user])
    count = 0
    for i in json_obj["Solution"]["BS_user_association"]:
        user_TP_coeficient[count] = (i["Throughput"]/
                                    (((100e6) * 4 * log(1 + (10**(30/10)), 2))))
        count += 1
    break
print(user_TP_coeficient)