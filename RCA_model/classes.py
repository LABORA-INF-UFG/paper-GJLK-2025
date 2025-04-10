class BS:
    def __init__(self, ID, TxPw, BW, range, Pkt_proc):
        self.ID = ID
        self.TxPw = TxPw
        self.BW = BW
        self.range = range
        self.Pkt_proc = Pkt_proc * 10**9

    def __str__(self):
        return "RUS {}: TxPW: {}\tBW: {}".format(self.ID, self.TxPw, self.BW)

class user:
    def __init__(self, ID, device, SE, application_ID, object_attention):
        self.ID = ID
        self.device = device
        self.SE = SE
        self.application_ID = application_ID
        self.object_attention = object_attention
    
    def my_SINR(self, bs_ID):
        for i in self.SE:
            if i["BS_ID"] == bs_ID:
                return i["SINR"]
    
    def __str__(self):
        return "User: {}\tSE: {}".format(self.ID, self.SE)

class MEC:
    def __init__(self, ID, CPU, RAM, HDD, GFLOPs, latency):
        self.ID = ID
        self.CPU = CPU
        self.RAM = RAM
        self.HDD = HDD
        self.GFLOPs = GFLOPs
        self.latency = latency
    def __str__(self):
        return "MEC: {}\tCPU: {}\tRAM: {}\tHDD: {}".format(self.ID, self.CPU, self.RAM, self.HDD)

class Object:
    def __init__(self, ID, length):
        self.ID = ID
        self.length = length
    def __str__(self):
        return "Object: {}\tLength: {}".format(self.ID, self.length)

