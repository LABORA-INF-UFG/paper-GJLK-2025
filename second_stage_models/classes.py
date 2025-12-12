class USER:
    def __init__(self, ID, SINR_to_gNBs, game_ID, game_instance, max_resolution, max_frame_rate):
        self.ID = ID
        self.SINR_to_gNBs = SINR_to_gNBs
        self.game = game_ID
        self.game_instance = game_instance
        self.max_resolution = max_resolution
        self.max_frame_rate = max_frame_rate
    def my_SE(self, BS_ID):
        return self.SINR_to_gNBs[str(BS_ID)]
    def my_game(self):
        return self.game
    def my_game_instance(self):
        return self.game_instance
    def my_max_resolution(self):
        return self.max_resolution
    def my_max_frame_rate(self):
        return self.max_frame_rate
    def my_ID(self):
        return self.ID

class GNB:
    def __init__(self, ID, TX_power, number_PRBs, PRB_BW):
        self.ID = ID
        self.TX_power = TX_power
        self.number_PRBs = number_PRBs
        self.PRB_BW = PRB_BW
    def my_ID(self):
        return self.ID
    def my_TX_power(self):
        return self.TX_power
    def my_number_PRBs(self):
        return self.number_PRBs
    def my_PRB_BW(self):
        return self.PRB_BW
    
class GAME:
    def __init__(self, ID, CPU_requirement, RAM_requirement, game_type):
        self.ID = ID
        self.CPU_requirement = CPU_requirement
        self.RAM_requirement = RAM_requirement
        self.game_type = game_type
    def my_ID(self):
        return self.ID
    def my_CPU_requirement(self):
        return self.CPU_requirement
    def my_RAM_requirement(self):
        return self.RAM_requirement
    def my_game_type(self):
        return self.game_type


class CN:
    def __init__(self, ID, CPU_capacity, GPU_capacity, RAM_capacity, compression_ratio, Network_capacity, Fixed_cost, Variable_cost):
        self.ID = ID
        self.CPU_capacity = CPU_capacity
        self.GPU_capacity = GPU_capacity
        self.RAM_capacity = RAM_capacity
        self.compression_ratio = compression_ratio
        self.Network_capacity = Network_capacity
        self.Fixed_cost = Fixed_cost
        self.Variable_cost = Variable_cost
    def my_Network_capacity(self):
        return self.Network_capacity
    def my_Fixed_cost(self):
        return self.Fixed_cost
    def my_Variable_cost(self):
        return self.Variable_cost
    def my_compression_ratio(self):
        return self.compression_ratio
    def my_ID(self):
        return self.ID
    def my_CPU_capacity(self):
        return self.CPU_capacity
    def my_GPU_capacity(self):
        return self.GPU_capacity
    def my_RAM_capacity(self):
        return self.RAM_capacity
    def my_compression_ratio(self):
        return self.compression_ratio

class PATH:
    def __init__(self, ID, source, destination, latency, bandwidth, links):
        self.ID = ID
        self.source = source
        self.destination = destination
        self.latency = latency
        self.bandwidth = bandwidth
        self.links = links
        self.links_list = []
        for link in self.links:
            self.links_list.append((link[0], link[1]))
    def my_ID(self):
        return self.ID
    def my_source(self):
        return self.source
    def my_destination(self):
        return self.destination
    def my_latency(self):
        return self.latency
    def my_bandwidth(self):
        return self.bandwidth
    def my_links(self):
        return self.links
    def my_links_list(self):
        return self.links_list

class OBJECT:
    def __init__(self, ID, length):
        self.ID = ID
        self.length = length
    def __str__(self):
        return "Object: {}\tLength: {}".format(self.ID, self.length)