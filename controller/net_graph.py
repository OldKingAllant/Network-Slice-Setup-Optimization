import unittest
import typing
import copy

from typing import List

class NetNode:
    def __init__(self):
        return
    
class NetSwitch(NetNode):
    def __init__(self, dpid):
        super().__init__()
        self.dpid = dpid

    def __eq__(self, value):
        if type(value) != type(self):
            return False
        return self.dpid == value.dpid

    def __str__(self):
        return f'Switch({self.dpid})'

class NetHost(NetNode):
    def __init__(self, ip):
        super().__init__()
        self.ip = ip

    def __eq__(self, value):
        if type(value) != type(self):
            return False
        return self.ip == value.ip

    def __ne__(self, value):
        return not (self.__eq__(value))

    def __str__(self):
        return f'Host({self.ip})'
    
class NetLink:
    def __init__(self, bw: int, delay: float, node0: NetNode, node1: NetNode, port1: str, port2: str):
        if node0 == node1:
            raise Exception("Attempting to link a node to itself")
        self.bw = bw
        self.delay = delay
        self.node0 = node0
        self.node1 = node1
        self.port1 = port1
        self.port2 = port2
    
    def __str__(self):
        return f'Link({self.node0} -> {self.node1})'

    def __eq__(self, value):
        if type(value) != type(self):
            return False
        return (self.node0 == value.node0 and self.node1 == value.node1) or \
        (self.node0 == value.node1 and self.node1 == value.node0)

    def contains_node(self, node: NetNode):
        return self.node0 == node or self.node1 == node

class NetGraph:
    def __init__(self):
        self.links: list[NetLink] = []
        self.nodes: list[NetNode] = []
        return
    
    def add_link(self, link: NetLink):
        if type(link.node0) == NetHost and type(link.node1) == NetHost:
            return
        if link in self.links:
            return
        self.links.append(link)
        return

    def add_node(self, node: NetNode):
        if node in self.nodes:
            return
        self.nodes.append(node)
        return

    def contains_node(self, node: NetNode):
        return node in self.nodes

    def contains_link(self, link: NetLink):
        return link in self.links

    def find_paths(self, host1: NetHost, host2: NetHost):
        if not host1 in self.nodes or not host2 in self.nodes:
            return None
        paths: list[list[NetLink]] = []
        starting_points = list(filter(lambda link: link.contains_node(host1), self.links))
        if len(starting_points) != 1:
            return None
        init_path = [starting_points[0]]
        def find_path_sub(self: NetGraph, visited_nodes: List[NetNode], curr_path: List[NetLink]):
            curr_link = curr_path[-1]
            next_node = None 
            if curr_link.node0 in visited_nodes:
                if curr_link.node1 in visited_nodes:
                    return
                next_node = curr_link.node1
            else:
                next_node = curr_link.node0
            if next_node == host2:
                paths.append(copy.deepcopy(curr_path))
                return
            possible_links = list(filter(lambda link: link.contains_node(next_node) \
                and link != curr_link and link not in curr_path, self.links))
            visited_nodes.append(next_node)
            for link in possible_links:
                new_path = copy.deepcopy(curr_path)
                if next_node == link.node1: #Maybe by the perspective of the user of the graph, 
                                            #if we put the link as is in the list, it would seem
                                            #like we are going in the wrong direction of the link.
                                            #I will simply swap the two nodes (and the ports)
                    link = copy.deepcopy(link)
                    temp = link.node0
                    link.node0 = link.node1
                    link.node1 = temp
                    temp_port = link.port1
                    link.port1 = link.port2
                    link.port2 = temp_port
                new_path.append(link)
                find_path_sub(self, copy.deepcopy(visited_nodes), new_path)
        find_path_sub(self, [host1], init_path)
        if len(paths) == 0:
            return None
        return paths

    def find_path(self, host1: NetHost, host2: NetHost, opt: str= "none"):
        opt_options = ["none", "bw", "delay"]
        if not opt in opt_options:
            raise Exception("Invalid optimization")
        paths = self.find_paths(host1, host2)
        if paths == None:
            return None
        if opt == "none":
            return paths[0]
        elif opt == "bw":
            paths.sort(key=lambda path: min(link.bw for link in path), reverse=True)
            if len(paths) > 1:
                curr_bw = min(link.bw for link in paths[0])
                paths = list(filter(lambda path: min(link.bw for link in path) == curr_bw, paths)) #Isolate all paths with bw equal to the current top one
                paths.sort(key=lambda path: sum(link.delay for link in path)) #Also sort them by delay
            return paths[0]
        paths.sort(key=lambda path: sum(link.delay for link in path))
        return paths[0]

class NetGraphTests(unittest.TestCase):
    def test_host_equal(self):
        host1 = NetHost('192.168.1.1')
        host2 = NetHost('192.168.1.1')
        self.assertTrue(host1 == host2)

    def test_host_not_equal(self):
        host1 = NetHost('192.168.1.1')
        host2 = NetHost('192.168.1.2')
        self.assertTrue(host1 != host2)

    def test_link_equal(self):
        link1 = NetLink(1, 1, NetHost('192.168.1.1'), NetHost('192.168.1.2'), 0, 0)
        link2 = NetLink(1, 1, NetHost('192.168.1.2'), NetHost('192.168.1.1'), 0, 0)
        self.assertTrue(link1 == link2)

    def test_link_not_equal(self):
        link1 = NetLink(1, 1, NetHost('192.168.1.1'), NetHost('192.168.1.2'), 0, 0)
        link2 = NetLink(1, 1, NetHost('192.168.1.3'), NetHost('192.168.1.1'), 0, 0)
        self.assertTrue(link1 != link2)

    def test_simple_graph(self):
        host1 = NetHost('192.168.1.1')
        host2 = NetHost('192.168.1.2')
        sw1 = NetSwitch('0')
        link1 = NetLink(1, 1, NetHost('192.168.1.1'), NetSwitch('0'), 0, 0)
        link2 = NetLink(1, 1, NetSwitch('0'), NetHost('192.168.1.2'), 0, 0)
        graph = NetGraph()
        graph.add_node(host1)
        graph.add_node(host2)
        graph.add_node(sw1)
        graph.add_link(link1)
        graph.add_link(link2)
        self.assertEqual(len(graph.nodes), 3)
        self.assertEqual(len(graph.links), 2)
        path = graph.find_path(host1, host2)
        self.assertNotEqual(path, None)
        print(list(map(lambda link: str(link), path)))
        self.assertEqual(graph.find_path(host1, NetHost('192.168.1.3')), None)

    def test_complex_graph(self):
        graph = NetGraph()
        central_switches = [NetSwitch('0'), NetSwitch('1')]
        graph.add_node(central_switches[0])
        graph.add_node(central_switches[1])
        num_switches = 6
        hosts_per_switch = 2
        for curr_switch in range(num_switches):
            new_switch = NetSwitch(str(curr_switch + 2))
            graph.add_node(new_switch)
            graph.add_link(NetLink(1, 1, new_switch, central_switches[0], 0, 0))
            graph.add_link(NetLink(1, 1, new_switch, central_switches[1], 0, 0))
            for curr_host in range(hosts_per_switch):
                curr_ip = f'192.168.{curr_switch+1}.{curr_host+1}'
                new_host = NetHost(curr_ip)
                graph.add_node(new_host)
                graph.add_link(NetLink(1, 1, new_host, new_switch, 0, 1))
        total_nodes = 2 + num_switches + num_switches * hosts_per_switch
        self.assertEqual(len(graph.nodes), total_nodes)
        path_bw    = graph.find_path(NetHost('192.168.1.1'), NetHost('192.168.6.1'), opt="bw")
        path_delay = graph.find_path(NetHost('192.168.1.1'), NetHost('192.168.6.1'), opt="delay")
        self.assertNotEqual(path_bw, None)
        self.assertNotEqual(path_delay, None)
        print()
        print(list(map(lambda link: str(link), path_bw)))
        print(list(map(lambda link: str(link), path_delay)))
        


if __name__ == "__main__":
    unittest.main()
