import json
import sys

def create_gNBs_file(n_gNBs):
    json_dict = {"gNBs": []}
    for i in range(n_gNBs):
        json_dict["gNBs"].append({
            "ID": i,
            "TX_power": 30,
            "number_PRBs": 273,
            "PRB_BW": 0.26
        })
    
    return json_dict

if __name__ == "__main__":
    n_gNBs = int(sys.argv[1])
    json_obj = create_gNBs_file(n_gNBs)
    json.dump(json_obj, open("{}_gNBs.json".format(n_gNBs), "w"), indent=4)