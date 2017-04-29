
class NodeCapacity:
    def __init__(self, json):
        self.cpu = json['cpu']
        self.memory = self.__convert_mem_str_to_int__(json['memory'])
        self.pods = json['pods']

    def __convert_mem_str_to_int__(self, mem_str):
        ''' unit of retrurned value is Mi '''
        value = float(mem_str[0:-2])
        unit = mem_str[-2:]
        if unit == 'Gi':
            value = value * 1024.
        if unit == 'Ki':
            value = value / 1024.0

        return value

class NodeSpec:
    def __init__(self, json):
        self.unschedulable = False
        if 'unschedulable' in json:
            self.unschedulable = json['unschedulable']

class NodeInfo:
    def __init__(self, json):
        self.kernel_version = json['kernelVersion']
        self.container_runtime_version = json['containerRuntimeVersion']
        self.kubelet_version = json['kubeletVersion']
        self.kube_proxy_version = json['kubeProxyVersion']

class Node(object):
    def __init__(self, json):
        self.labels = json['metadata']['labels']
        self.name = json['metadata']['name']
        self.capacity = NodeCapacity(json['status']['capacity'])
        self.node_info = NodeInfo(json['status']['nodeInfo'])
        self.spec = NodeSpec(json['spec'])
        self.conditions = json['status']['conditions']
        self.pod_num = 0
        self.mem_limit_used = 0.0

    def is_ready(self):
        for condition in self.conditions:
            if condition['type'] == 'Ready' and condition['status'] == 'True':
                return True
        else:
            return False

