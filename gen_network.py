import json

def generate_switch_rules_from_topology(topology_file):
    """
    Generates switch rules based on the network topology defined in a JSON file.

    Args:
        topology_file (str): Path to the JSON file containing the network topology.

    Returns:
        dict: A dictionary where keys are switch names and values are lists of rules
              for that switch.
    """

    with open(topology_file, 'r') as f:
        topology = json.load(f)

    hosts = topology['hosts']
    switches = topology['switches']
    links = topology['links']

    switch_rules = {}

    for switch_name in switches:
        switch_rules[switch_name] = []

    # Create a dictionary to store host IPs and MACs for easy lookup
    host_info = {}
    for host_name, host_data in hosts.items():
        host_info[host_name] = {'ip': host_data['ip'].split('/')[0], 'mac': host_data['mac']}

    # Iterate through the links to create forwarding rules
    for link in links:
        node1, node2 = link

        # Determine the type of each node and extract relevant information
        if node1 in switches:
            switch1 = node1
            if node2 in host_info:
                host = node2
                port = 1  # Assuming port 1 for host connections
                dst_ip = host_info[host]['ip']
                dst_mac = host_info[host]['mac']

                rule = {
                    "table": "MyIngress.ipv4_lpm",
                    "match": {"hdr.ipv4.dstAddr": (dst_ip, 32)},
                    "action_name": "MyIngress.ipv4_forward",
                    "action_params": {"dstAddr": dst_mac, "port": port}
                }
                switch_rules[switch1].append(rule)
            else:
                # Handle switch-to-switch links
                parts = node2.split('-')
                if len(parts) == 2:
                    next_hop_switch = parts[0]
                    port = int(parts[1][1:])  # Extract port number from "pX"
                    # Add a rule to forward to the next hop switch (assuming you have a way to determine the MAC)
                    # You might need a separate function to determine the MAC address of the next hop switch
                    next_hop_mac = "00:00:00:00:00:01"  # Replace with actual MAC
                    rule = {
                        "table": "MyIngress.ipv4_lpm",
                        "match": {"hdr.ipv4.dstAddr": ("10.0.0.0", 16)},  # Match any IP in the 10.0.0.0/16 range
                        "action_name": "MyIngress.ipv4_forward",
                        "action_params": {"dstAddr": next_hop_mac, "port": port}
                    }
                    switch_rules[switch1].append(rule)

        elif node2 in switches:
            switch2 = node2
            if node1 in host_info:
                host = node1
                port = 1  # Assuming port 1 for host connections
                dst_ip = host_info[host]['ip']
                dst_mac = host_info[host]['mac']

                rule = {
                    "table": "MyIngress.ipv4_lpm",
                    "match": {"hdr.ipv4.dstAddr": (dst_ip, 32)},
                    "action_name": "MyIngress.ipv4_forward",
                    "action_params": {"dstAddr": dst_mac, "port": port}
                }
                switch_rules[switch2].append(rule)
            else:
                # Handle switch-to-switch links
                parts = node1.split('-')
                if len(parts) == 2:
                    next_hop_switch = parts[0]
                    port = int(parts[1][1:])  # Extract port number from "pX"
                    # Add a rule to forward to the next hop switch (assuming you have a way to determine the MAC)
                    # You might need a separate function to determine the MAC address of the next hop switch
                    next_hop_mac = "00:00:00:00:00:01"  # Replace with actual MAC
                    rule = {
                        "table": "MyIngress.ipv4_lpm",
                        "match": {"hdr.ipv4.dstAddr": ("10.0.0.0", 16)},  # Match any IP in the 10.0.0.0/16 range
                        "action_name": "MyIngress.ipv4_forward",
                        "action_params": {"dstAddr": next_hop_mac, "port": port}
                    }
                    switch_rules[switch2].append(rule)

    return switch_rules

# Example usage:
topology_file = '/home/p4/SelfHealingPMU/topology.json'
all_switch_rules = generate_switch_rules_from_topology(topology_file)

# Print the generated rules for each switch
for switch, rules in all_switch_rules.items():
    print(f"Rules for switch {switch}:")
    for rule in rules:
        print(rule)
    print("\n")