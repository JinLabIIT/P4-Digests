import networkx as nx
import matplotlib.pyplot as plt
import random
import csv
import time

class PDC:
    def __init__(self, pdc_id, ip_addr, switch__list, PMU_list, curr_traffic, capacity):
        self.pdc_id = pdc_id
        self.ip_addr = ip_addr
        self.switch_list = switch__list
        self.PMU_list = PMU_list
        self.capacity = capacity
        self.curr_traffic = curr_traffic
    
    def __str__(self):
        return f"PDC({self.pdc_id}), Switches: {self.switch_list} PMUs:{self.PMU_list}"
    
    def pdc_id(self):
        return self.pdc_id
    
    def ip_addr(self):
        return self.ip_addr

    def PMU_list(self):
        return self.PMU_list
    
    def add_pmu(self, pmu_id):
        self.PMU_list.append(pmu_id)
    
    def switch_list(self):
        return self.switch_list
    
    def capacity(self):
        return self.capacity
    
    def atCapacity(self):
        if (self.PMU_list.len() < self.capacity):
            return False
        else:
            return True
        
    def increment_traffic(self, traffic):
        if (self.curr_traffic + traffic) < self.capacity:
            self.curr_traffic += traffic
        else:
            print(f"PDC {self.pdc_id} is at full capacity!")
    
class PMU:
    def __init__(self, pmu_id,  ip_addr, switch_list, pdc_id, adj_busses, dir_busses):
        self.pmu_id = pmu_id
        self.switch_list = switch_list
        self.pdc_id = pdc_id
        self.ip_addr = ip_addr
        self.adj_busses = adj_busses
        self.dir_busses = dir_busses

    def __str__(self):
        return f"PMU({self.pmu_id}), PDC: {self.pdc_id} Switches: {self.switch_list}"
    
    def pmu_id(self):
        return self.pmu_id
    
    def pdc_id(self):
        return self.pdc_id
    
    def switch_list(self):
        return self.switch_list
    
    def ip_addr(self):
        return self.ip_addr
    
class Switch:
    def __init__(self, switch_id, ip_addr, pdc_list, pmu_list, switch_list, cMatrix, Icapacity, Ocapacity):
        self.switch_id = switch_id
        self.ip_addr = ip_addr
        self.pdc_list = pdc_list
        self.pmu_list = pmu_list
        self.switch_list = switch_list
        self.cMatrix = cMatrix
        self.Icapacity = Icapacity
        self.Ocapacity = Ocapacity

    def __str__(self):
        return f"Switch({self.switch_id}), PDCs: {self.pdc_list}, PMUs: {self.pmu_list}"
    
    def switch_id(self):
        return self.switch_id
    
    def pdc_list(self):
        return self.pdc_list
    
    def pmu_list(self):
        return self.pmu_list
    
    def switch_list(self):
        return self.switch_list
    
    def capacity(self):
        return self.capacity
    
    def ip_addr(self):
        return self.ip_addr
    
    def atCapacity(self):
        if(self.pdc_list.len() < self.Ocapacity or self.pmu_list.len() < self.Icapacity):
            return False
        else:
            return True
    
    def isConnected(self, pdc_id, pmu_id):
        if (self.cMatrix[pdc_id][pmu_id] == 1):
            return True
        else:
            return False
        
    def new_connection(self, pdc_id, pmu_id):
        if(pmu_id in self.pmu_list):
            pass
        else:
            self.pmu_list.append(pmu_id)
        self.cMatrix[pdc_id][pmu_id] = 1


class Network:
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def add_pmu(self, pmu):
        self.graph.add_node(pmu.pmu_id, type='PMU', obj=pmu, adj_busses=pmu.adj_busses, dir_busses=pmu.dir_busses)
    
    def add_pdc(self, pdc):
        self.graph.add_node(pdc.pdc_id, type='PDC', obj=pdc)
    
    def add_switch(self, switch):
        self.graph.add_node(switch.switch_id, type='Switch', obj=switch, Icapacity=switch.Icapacity, Ocapacity=switch.Ocapacity)
    
    def add_pmu_to_switch(self, pmu, switch, traffic):
        self.graph.add_edge(pmu.pmu_id, switch.switch_id, weight=traffic)
        switch.pmu_list.append(pmu.pmu_id)
    
    def add_pdc_to_switch(self, switch, pdc, traffic):
        self.graph.add_edge(switch.switch_id, pdc.pdc_id, weight=traffic)
        switch.pdc_list.append(pdc.pdc_id)

    def add_switch_to_switch(self, switch1, switch2, traffic):
        self.graph.add_edge(switch1.switch_id, switch2.switch_id, weight=traffic)
        switch1.switch_list.append(switch2.switch_id)
        switch2.switch_list.append(switch1.switch_id)

    def is_connected(self, pmu_id):
        if pmu_id not in self.graph:
            print(f"{pmu_id} is not in the network.")
            return False

        for switch in self.graph.successors(pmu_id):
            if self.graph.nodes[switch]['type'] == 'Switch':
                for pdc in self.graph.successors(switch):
                    if self.graph.nodes[pdc]['type'] == 'PDC':
                        print(f"{pmu_id} is connected to {pdc} through {switch}.")
                        return True
        
        print(f"{pmu_id} is not connected to any PDC.")
        return False
    
    def connect(self, removed_pdc_ip, log_file="routing_changes.log"):
        def is_connected_to_pdc(pmu_id, target_pdc_id):
            """
            Check if the PMU is connected to its target PDC through any switch.
            """
            for switch_id in self.graph.successors(pmu_id):
                if self.graph.nodes[switch_id]['type'] == 'Switch':
                    for pdc_id in self.graph.successors(switch_id):
                        if self.graph.nodes[pdc_id]['type'] == 'PDC' and pdc_id == target_pdc_id:
                            return True
            return False

        def find_and_connect_pdc(pmu_id, target_pdc_id):
            """
            Try to connect the PMU to its target PDC or any available alternative PDC.
            """
            pmu = self.graph.nodes[pmu_id]['obj']

            for switch_id in self.graph.successors(pmu_id):
                if self.graph.nodes[switch_id]['type'] == 'Switch':
                    switch = self.graph.nodes[switch_id]['obj']

                    # Check all PDCs connected to this switch
                    for pdc_id in self.graph.successors(switch_id):
                        if self.graph.nodes[pdc_id]['type'] == 'PDC':
                            pdc = self.graph.nodes[pdc_id]['obj']
                            if len(list(self.graph.predecessors(pdc_id))) < pdc.capacity:
                                self.graph.add_edge(switch_id, pdc_id, weight=1)
                                pdc.increment_traffic(1)
                                print(f"Routing updated: {pmu_id} -> {switch_id} -> {pdc_id}. Current traffic: {pdc.curr_traffic}")
                                return pdc_id

                    # Check neighboring switches for available PDCs
                    for neighbor_id in switch.switch_list:
                        if neighbor_id in self.graph and self.graph.nodes[neighbor_id]['type'] == 'Switch':
                            for neighbor_pdc_id in self.graph.successors(neighbor_id):
                                if self.graph.nodes[neighbor_pdc_id]['type'] == 'PDC':
                                    neighbor_pdc = self.graph.nodes[neighbor_pdc_id]['obj']
                                    if len(list(self.graph.predecessors(neighbor_pdc_id))) < neighbor_pdc.capacity:
                                        self.graph.add_edge(neighbor_id, neighbor_pdc_id, weight=1)
                                        neighbor_pdc.increment_traffic(1)
                                        print(f"Connected PMU {pmu_id} to PDC {neighbor_pdc_id} through neighbor Switch {neighbor_id}. Current traffic: {neighbor_pdc.curr_traffic}")
                                        return neighbor_pdc_id

            # If target PDC is unavailable, attempt to connect to any alternative PDC
            for switch_id in self.graph.successors(pmu_id):
                if self.graph.nodes[switch_id]['type'] == 'Switch':
                    for pdc_id in self.graph.successors(switch_id):
                        if self.graph.nodes[pdc_id]['type'] == 'PDC':
                            pdc = self.graph.nodes[pdc_id]['obj']
                            if len(list(self.graph.predecessors(pdc_id))) < pdc.capacity:
                                self.graph.add_edge(switch_id, pdc_id, weight=1)
                                pdc.increment_traffic(1)
                                print(f"Routed PMU {pmu_id} to alternative PDC {pdc_id} via Switch {switch_id}. Current traffic: {pdc.curr_traffic}")
                                return pdc_id

            print(f"No available PDC for PMU {pmu_id}.")
            return


        # Open the log file for recording changes
        with open(log_file, "w") as log:

            # Iterate through all PMUs
            for pmu_id, data in self.graph.nodes(data=True):
                if data['type'] != 'PMU':
                    continue  # Skip nodes that are not PMUs

                pmu = data['obj']
                target_pdc_id = pmu.pdc_id  # The PDC this PMU wants to connect to

                if target_pdc_id not in self.graph:
                    # Target PDC has been removed, attempt to reroute
                    print(f"PDC {target_pdc_id} has been removed. Attempting to reroute {pmu_id}.")

                    result = find_and_connect_pdc(pmu_id, target_pdc_id)
                    pmu_ip = self.graph.nodes[pmu_id]['obj'].ip_addr
                    new_pdc_ip = self.graph.nodes[result]['obj'].ip_addr
                    log.write(f"{pmu_ip}, " + f"{removed_pdc_ip}, " + f"{new_pdc_ip} " + "\n")

                elif is_connected_to_pdc(pmu_id, target_pdc_id):
                    # PMU is already connected to its target PDC
                    print(f"{pmu_id} is already connected to its target PDC {target_pdc_id}.")

                else:
                    # PMU's target PDC exists, but it's not connected; update route
                    print(f"{pmu_id} is not connected to its target PDC {target_pdc_id}. Updating route.")
                    result = find_and_connect_pdc(pmu_id, target_pdc_id)



    def visualize_network(network):
        plt.figure(figsize=(10, 10))
        
        pos = nx.spring_layout(network.graph)  # Position nodes using a spring layout
        
        # Get lists of nodes by type
        pmu_nodes = [node for node, data in network.graph.nodes(data=True) if data['type'] == 'PMU']
        switch_nodes = [node for node, data in network.graph.nodes(data=True) if data['type'] == 'Switch']
        pdc_nodes = [node for node, data in network.graph.nodes(data=True) if data['type'] == 'PDC']
        
        # Draw PMU nodes (as circles)
        nx.draw_networkx_nodes(network.graph, pos, nodelist=pmu_nodes, node_size=500, node_color='lightblue', label='PMUs', node_shape='o')
        
        # Draw Switch nodes (as squares)
        nx.draw_networkx_nodes(network.graph, pos, nodelist=switch_nodes, node_size=800, node_color='orange', label='Switches', node_shape='s')
        
        # Draw PDC nodes (as triangles)
        nx.draw_networkx_nodes(network.graph, pos, nodelist=pdc_nodes, node_size=600, node_color='green', label='PDCs', node_shape='^')
        
        pdc_colors = {pdc: (random.random(), random.random(), random.random()) for pdc in pdc_nodes} 

        for pmu in pmu_nodes:
            for switch in network.graph.successors(pmu):
                if network.graph.nodes[switch]['type'] == 'Switch':
                    for pdc in network.graph.successors(switch):
                        if network.graph.nodes[pdc]['type'] == 'PDC':
                            edge_color = pdc_colors[pdc]  # Get color assigned to this PDC
                            nx.draw_networkx_edges(network.graph, pos, edgelist=[(pmu, switch), (switch, pdc)], 
                                                width=2, edge_color=[edge_color], style='solid')


        # Draw the edges with their weights (traffic)
        edges = network.graph.edges(data=True)
        weights = [edge_data['weight'] for _, _, edge_data in edges]
        nx.draw_networkx_edges(network.graph, pos, edgelist=edges, width=weights, edge_color='gray')
        
        # Label the nodes
        nx.draw_networkx_labels(network.graph, pos, font_size=10, font_family='sans-serif')
        
        # Create edge labels (traffic weights)
        edge_labels = {(u, v): f"Traffic: {d['weight']}" for u, v, d in edges}
        nx.draw_networkx_edge_labels(network.graph, pos, edge_labels=edge_labels, font_size=8)
        
        # Add a legend
        plt.legend(scatterpoints=1, loc='best', fontsize='x-large')
        
        # Display the graph
        plt.title('PMU, Switch, and PDC Network')
        plt.axis('off')  # Turn off the axis
        plt.show()

    def export_pmu_details(self, filename="pmu_details.csv"):
        """
        Exports PMU details to a CSV file with PMU ID and the buses it can observe.
        """
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["PMU_ID", "Direct_Busses", "Adjacent_Busses"])

            for pmu_id, data in self.graph.nodes(data=True):
                if data['type'] == 'PMU':
                    pmu = data['obj']
                    writer.writerow([pmu_id, ", ".join(map(str, pmu.dir_busses)), ", ".join(map(str, pmu.adj_busses))])

        print(f"PMU details exported successfully to {filename}")

    def find_critical_pmus(self):
        """
        Identifies critical PMUs - if a PMU is removed, does a bus become unobservable?
        Measures the execution time.
        """
        start_time = time.time()  # Start timing

        bus_observability = {}

        # Create a mapping of which PMUs observe which buses
        for pmu_id, data in self.graph.nodes(data=True):
            if data['type'] == 'PMU':
                pmu = data['obj']
                all_busses = set(pmu.dir_busses) | set(pmu.adj_busses)  # Combine direct & adjacent buses

                for bus in all_busses:
                    if bus not in bus_observability:
                        bus_observability[bus] = set()
                    bus_observability[bus].add(pmu_id)

        critical_pmus = []

        # Identify PMUs whose removal causes loss of bus observability
        for pmu_id, data in self.graph.nodes(data=True):
            if data['type'] == 'PMU':
                pmu = data['obj']
                all_busses = set(pmu.dir_busses) | set(pmu.adj_busses)

                for bus in all_busses:
                    if len(bus_observability[bus]) == 1 and pmu_id in bus_observability[bus]:
                        critical_pmus.append(pmu_id)
                        break  # If this PMU is critical for even one bus, mark it critical

        end_time = time.time()  # End timing
        execution_time = end_time - start_time  # Compute elapsed time

        print(f"Critical PMUs: {critical_pmus}")
        print(f"Execution time: {execution_time:.6f} seconds")

        return critical_pmus

def create_network():
    # Create the network object
    network = Network()
    
    # Create some PMUs
    pmu1 = PMU("PMU1", '0x0a000001', [], "PDC1", ["Bus1", "Bus3"], ["Bus2"])
    pmu2 = PMU("PMU2", '0x0a000002', [], "PDC1", ["Bus4", "Bus6"], ["Bus5"])
    pmu3 = PMU("PMU3", '0x0a000003', [], "PDC2", ["Bus7", "Bus9"], ["Bus8"])
    pmu4 = PMU("PMU4", '0x0a000004', [], "PDC2", ["Bus9", "Bus11"], ["Bus10"])
    pmu5 = PMU("PMU5", '0x0a000005', [], "PDC3", ["Bus11", "Bus13"], ["Bus12"])
    pmu6 = PMU("PMU6", '0x0a000006', [], "PDC3", ["Bus13", "Bus15"], ["Bus14"])
    pmu7 = PMU("PMU7", '0x0a000007', [], "PDC4", ["Bus15", "Bus17"], ["Bus16"])
    pmu8 = PMU("PMU8", '0x0a000008', [], "PDC5", ["Bus17"], ["Bus18"])

    # Create some PDCs with capacity for 2 PMUs
    pdc1 = PDC("PDC1", '0x0a000009', [], [], 0, capacity=3)
    pdc2 = PDC("PDC2", '0x0a00000a', [], [], 0, capacity=3)
    pdc3 = PDC("PDC3", '0x0a00000b', [], [], 0, capacity=2)
    pdc4 = PDC("PDC4", '0x0a00000c', [], [], 0, capacity=2)
    pdc5 = PDC("PDC5", '0x0a00000d', [], [], 0, capacity=2)
    
    # Create a Switch with some arbitrary capacity and connection matrix
    cMatrix = [[0 for _ in range(3)] for _ in range(3)]  # Empty connection matrix
    switch1 = Switch("Switch1", '0x0a00000e', [], [], [], cMatrix, Icapacity=3, Ocapacity=6)
    switch2 = Switch("Switch2", '0x0a00000f', [], [], [],cMatrix, Icapacity=3, Ocapacity=6)
    switch3 = Switch("Switch3", '0x0a000010', [], [], [], cMatrix, Icapacity=3, Ocapacity=6)
    
    # Add PMUs, PDCs, and Switches to the network
    network.add_pmu(pmu1)
    network.add_pmu(pmu2)
    network.add_pmu(pmu3)
    network.add_pmu(pmu4)
    network.add_pmu(pmu5)
    network.add_pmu(pmu6)
    network.add_pmu(pmu7)
    network.add_pmu(pmu8)
    
    network.add_pdc(pdc1)
    network.add_pdc(pdc2)
    network.add_pdc(pdc3)
    network.add_pdc(pdc4)
    network.add_pdc(pdc5)
    
    network.add_switch(switch1)
    network.add_switch(switch2)
    network.add_switch(switch3)
    
    # Add connections (initial routing)
    network.add_pmu_to_switch(pmu1, switch1, traffic=1)
    network.add_pmu_to_switch(pmu2, switch1, traffic=1)
    network.add_pmu_to_switch(pmu3, switch1, traffic=1)

    network.add_pmu_to_switch(pmu4, switch2, traffic=1)
    network.add_pmu_to_switch(pmu5, switch2, traffic=1)
    network.add_pmu_to_switch(pmu6, switch2, traffic=1)
    
    network.add_pmu_to_switch(pmu7, switch3, traffic=1)
    network.add_pmu_to_switch(pmu8, switch3, traffic=1)
    
    network.add_pdc_to_switch(switch1, pdc1, traffic=2)
    network.add_pdc_to_switch(switch1, pdc2, traffic=2)

    network.add_pdc_to_switch(switch2, pdc3, traffic=2)
    network.add_pdc_to_switch(switch2, pdc4, traffic=2)

    network.add_pdc_to_switch(switch3, pdc5, traffic=2)

    network.add_switch_to_switch(switch1, switch2, traffic=3)
    network.add_switch_to_switch(switch2, switch3, traffic=3)
    
    return network

def remove_random_pdc(network):
    # Get all PDCs in the network
    pdc_nodes = [node for node, data in network.graph.nodes(data=True) if data['type'] == 'PDC']
    
    # Randomly select and remove one PDC
    if pdc_nodes:
        pdc_to_remove = random.choice(pdc_nodes)
        pdc_ip = network.graph.nodes[pdc_to_remove]['obj'].ip_addr
        network.graph.remove_node(pdc_to_remove)
        print(f"PDC {pdc_to_remove} has been removed from the network.")
        return pdc_ip
    else:
        print("No PDCs available to remove.")
    
def main():
    # Set up the initial network
    network = create_network()
    
    # Visualize the network before PDC removal
    print("Network before PDC removal:")
    network.visualize_network()  # Visualize before removal
    
    # Remove a random PDC
    ip = remove_random_pdc(network)
    find_ciritical_pmus = network.find_critical_pmus()  # Identify critical PMUs
    print(f"Critical PMUs after PDC removal: {find_ciritical_pmus}")
    
    # Visualize the network after PDC removal
    print("Network after PDC removal:")
    network.visualize_network()  # Visualize after removal
    
    # Call the decentralized routing method to fix connections
    network.connect(ip)
    
    # Visualize the fixed network
    print("Network after fixing decentralized routing:")
    network.visualize_network()  # Visualize after re-routing

if __name__ == "__main__":
    main()