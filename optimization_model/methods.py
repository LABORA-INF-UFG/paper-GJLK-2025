import json
import pandas as pd
from classes import BS, user, MEC

def read_BSs(file):
    json_obj = json.load(open(file, 'r'))
    BSs = []
    for i in json_obj["BSs"]:
        BSs.append(BS(i["ID"], i["TxPw"], i["BW"], i["range"], i["Pkt_proc"]))
    return BSs

def read_users(file):
    json_obj = json.load(open(file, 'r'))
    users = []
    for i in json_obj["users"]:
        object_attention = {}
        df = pd.read_csv(open("/home/gabriel/workspace/QoE-based-Resource-Allocation/input_scenarios/my_rating.csv", "r"))
        for index, row in df.iterrows():
            if row['userId'] == i["ID"]:
                object_attention[int(row['objectId'])] = int(row['rating'])
        users.append(user(i["ID"], i["device"], i["SINR"], i["application_ID"], object_attention))
    return users

def read_MEC(file):
    json_obj = json.load(open(file, 'r'))
    MEC_servers = []
    for i in json_obj["MEC_servers"]:
        MEC_servers.append(MEC(i["ID"], i["CPU"], i["RAM"], i["HDD"], i["GFLOPs"], i["latency"]))
    return MEC_servers