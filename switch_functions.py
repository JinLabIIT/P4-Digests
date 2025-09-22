import networkx as nx
import matplotlib.pyplot as plt
import random
import csv

import time
import json

#Network class for netowrkx (contains controller functions identify critical PMUs and reroute PMUs)
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
    
    #load network from .json file
    def load_network(self, filename):
        try:
            with open(filename, 'r') as file:
                topology = json.load(file)
        except FileNotFoundError:
            print(f"Error: Topology file '{filename}' not found.")
            return
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from '{filename}'.")
            return

        # Add hosts (PMUs, PDCs, generic Hosts)
        for host_id, attrs in topology.get("hosts", {}).items():
            ip = attrs.get("ip", "")
            
            if ip.startswith("10.0.1."): # PMU
                pmu = PMU(pmu_id=host_id, ip_addr=ip,
                          # switch_list, pdc_id are typically dynamic, initialize as None/empty
                          switch_list=[], 
                          pdc_id=None, 
                          adj_busses=attrs.get("adj_busses", []),
                          dir_busses=attrs.get("dir_busses", []))
                self.add_pmu(pmu)
            elif ip.startswith("10.0.2."): # PDC
                pdc = PDC(pdc_id=host_id, ip_addr=ip,
                          # switch_list, PMU_list are dynamic
                          switch_list=[], 
                          PMU_list=[], 
                          curr_traffic=attrs.get("curr_traffic", 0),
                          capacity=attrs.get("capacity", 3))
                self.add_pdc(pdc)
            else: # Generic Host
                # For generic hosts, we add them directly.
                # If they need to be objects, a GenericHost class would be needed.
                self.graph.add_node(host_id, type="Host", obj=None, **attrs) # obj=None or a GenericHost object

        # Add switches
        for switch_id, attrs in topology.get("switches", {}).items():
            switch_obj = Switch(
                switch_id=switch_id,
                ip_addr=attrs.get("ip", ""), # Switches might have IPs
                # pdc_list, pmu_list, switch_list are dynamic
                pdc_list=[],
                pmu_list=[],
                switch_list=[],
                conn_Matrix=attrs.get("conn_Matrix", {}),
                Icapacity=attrs.get("Icapacity", 10), 
                Ocapacity=attrs.get("Ocapacity", 10)
            )
            self.add_switch(switch_obj)

        # Add links
        for link_data in topology.get("links", []):
            # Flexible link definition: can be [node1, node2] or [node1, node2, weight]
            # or {"source": "n1", "target": "n2", "weight": w}
            node1_name, node2_name, traffic = None, None, 1 # Default traffic

            if isinstance(link_data, (list, tuple)):
                if len(link_data) < 2:
                    print(f"Warning: Malformed link data (list/tuple): {link_data}. Skipping.")
                    continue
                node1_name, node2_name = link_data[0], link_data[1]
                if len(link_data) > 2 and isinstance(link_data[2], (int, float)):
                    traffic = link_data[2]
            elif isinstance(link_data, dict):
                node1_name = link_data.get('source')
                node2_name = link_data.get('target')
                traffic = link_data.get('weight', link_data.get('traffic', 1)) # common keys for weight
                if not node1_name or not node2_name:
                    print(f"Warning: Malformed link data (dict): {link_data}. Missing source or target. Skipping.")
                    continue
            else:
                print(f"Warning: Unknown link data format: {link_data}. Skipping.")
                continue

            # Strip port info (e.g., s1-p1 -> s1)
            node1_base = node1_name.split('-')[0]
            node2_base = node2_name.split('-')[0]

            if node1_base not in self.graph or node2_base not in self.graph:
                print(f"Warning: Node(s) '{node1_base}' or '{node2_base}' for link not found in graph. Skipping link.")
                continue

            node1_attrs = self.graph.nodes[node1_base]
            node2_attrs = self.graph.nodes[node2_base]
            
            node1_type = node1_attrs.get('type')
            node2_type = node2_attrs.get('type')

            # Crucially, get the actual objects
            obj1 = node1_attrs.get('obj')
            obj2 = node2_attrs.get('obj')

            # Check if objects exist for types that require them for specific connection logic
            if node1_type in ['PMU', 'PDC', 'Switch'] and not obj1:
                print(f"Warning: Object 'obj' not found for node {node1_base} of type {node1_type}. Adding generic edge.")
                self.graph.add_edge(node1_base, node2_base, weight=traffic)
                continue
            if node2_type in ['PMU', 'PDC', 'Switch'] and not obj2:
                print(f"Warning: Object 'obj' not found for node {node2_base} of type {node2_type}. Adding generic edge.")
                self.graph.add_edge(node1_base, node2_base, weight=traffic)
                continue

            # Specific connection logic using objects
            if node1_type == 'PMU' and node2_type == 'Switch':
                self.add_pmu_to_switch(obj1, obj2, traffic=traffic)
            elif node1_type == 'Switch' and node2_type == 'PDC':
                self.add_pdc_to_switch(obj1, obj2, traffic=traffic)
            elif node1_type == 'Switch' and node2_type == 'Switch':
                self.add_switch_to_switch(obj1, obj2, traffic=traffic)
            # Handle Switch to PMU (if PMUs can be controlled, less common for data flow)
            # elif node1_type == 'Switch' and node2_type == 'PMU':
            #     print(f"Info: Switch-to-PMU link from {node1_base} to {node2_base}. Check if this is intended.")
            #     self.graph.add_edge(node1_base, node2_base, weight=traffic) # Generic edge for now
            else:
                # For other types of links (e.g., Host-Switch, or if types are unexpected)
                # print(f"Adding generic edge between {node1_base} ({node1_type}) and {node2_base} ({node2_type})")
                self.graph.add_edge(node1_base, node2_base, weight=traffic)

        print(f"Network topology successfully loaded from '{filename}'.")
    
    def connect(self, removed_pdc_ip):
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

        updated_routes = {}  # Dictionary to store updated routes

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

                if result is not None:  # Check if a new PDC was found
                    print(f"Successfully rerouted {pmu_id} to PDC {result}.")
                    # Update the PMU's pdc_id to the new PDC
                    pmu.pdc_id = result
                    updated_routes[pmu_id] = result  # Store the new route
                else:
                    print(f"Failed to reroute {pmu_id} after removing PDC {removed_pdc_ip}.")
                    updated_routes[pmu_id] = None  # Indicate that rerouting failed

            elif is_connected_to_pdc(pmu_id, target_pdc_id):
                # PMU is already connected to its target PDC
                print(f"{pmu_id} is already connected to its target PDC {target_pdc_id}.")
                updated_routes[pmu_id] = target_pdc_id  # Route is unchanged

            else:
                # PMU's target PDC exists, but it's not connected; update route
                print(f"{pmu_id} is not connected to its target PDC {target_pdc_id}. Updating route.")
                result = find_and_connect_pdc(pmu_id, target_pdc_id)
                if result is not None:
                    updated_routes[pmu_id] = result
                else:
                    updated_routes[pmu_id] = None

        return updated_routes
    
    def remove_random_pdc(self):
        # Get all PDCs in the network
        pdc_nodes = [node for node, data in self.graph.nodes(data=True) if data['type'] == 'PDC']
        
        # Randomly select and remove one PDC
        if pdc_nodes:
            pdc_to_remove = random.choice(pdc_nodes)
            pdc_ip = self.graph.nodes[pdc_to_remove]['obj'].ip_addr
            self.graph.remove_node(pdc_to_remove)
            print(f"PDC {pdc_to_remove} has been removed from the network.")
            return pdc_ip
        else:
            print("No PDCs available to remove.")
            return None   

    def visualize_network(self):
        plt.figure(figsize=(10, 10))
        
        pos = nx.spring_layout(self.graph, k=1) 
        
        # Get lists of nodes by type
        pmu_nodes = [node for node, data in self.graph.nodes(data=True) if data['type'] == 'PMU']
        switch_nodes = [node for node, data in self.graph.nodes(data=True) if data['type'] == 'Switch']
        pdc_nodes = [node for node, data in self.graph.nodes(data=True) if data['type'] == 'PDC']
        
        # Draw PMU nodes (as circles)
        nx.draw_networkx_nodes(self.graph, pos, nodelist=pmu_nodes, node_size=500, node_color='lightblue', label='PMUs', node_shape='o')
        
        # Draw Switch nodes (as squares)
        nx.draw_networkx_nodes(self.graph, pos, nodelist=switch_nodes, node_size=800, node_color='orange', label='Switches', node_shape='s')
        
        # Draw PDC nodes (as triangles)
        nx.draw_networkx_nodes(self.graph, pos, nodelist=pdc_nodes, node_size=600, node_color='green', label='PDCs', node_shape='^')
        
        pdc_colors = {pdc: (random.random(), random.random(), random.random()) for pdc in pdc_nodes} 

        for pmu in pmu_nodes:
            for switch in self.graph.successors(pmu):
                if self.graph.nodes[switch]['type'] == 'Switch':
                    for pdc in self.graph.successors(switch):
                        if self.graph.nodes[pdc]['type'] == 'PDC':
                            edge_color = pdc_colors[pdc]  # Get color assigned to this PDC
                            nx.draw_networkx_edges(self.graph, pos, edgelist=[(pmu, switch), (switch, pdc)], 
                                                width=2, edge_color=[edge_color], style='solid')


        # Draw the edges with their weights (traffic)
        edges = self.graph.edges(data=True)
        weights = [edge_data['weight'] for _, _, edge_data in edges]
        nx.draw_networkx_edges(self.graph, pos, edgelist=edges, width=weights, edge_color='gray')
        
        # Label the nodes
        nx.draw_networkx_labels(self.graph, pos, font_size=10, font_family='sans-serif')
        
        # Create edge labels (traffic weights)
        edge_labels = {(u, v): f"Traffic: {d['weight']}" for u, v, d in edges}
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_size=8)
        
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


#Objects for the Network (switches, PDCs, PMUs)   
class PDC:
    def __init__(self, pdc_id, ip_addr, switch_list, PMU_list, curr_traffic, capacity):
        self.pdc_id = pdc_id
        self.ip_addr = ip_addr
        self.switch_list = switch_list
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
    def __init__(self, switch_id, ip_addr, pdc_list, pmu_list, switch_list, conn_Matrix, Icapacity, Ocapacity):
        self.switch_id = switch_id
        self.ip_addr = ip_addr
        self.pdc_list = pdc_list
        self.pmu_list = pmu_list
        self.switch_list = switch_list
        self.conn_Matrix = conn_Matrix
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
        if (self.conn_Matrix[pdc_id][pmu_id] == 1):
            return True
        else:
            return False
        
    def new_connection(self, pdc_id, pmu_id):
        if(pmu_id in self.pmu_list):
            pass
        else:
            self.pmu_list.append(pmu_id)
        self.conn_Matrix[pdc_id][pmu_id] = 1
