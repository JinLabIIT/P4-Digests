from switch_functions import Network as net

def main():
    # Set up the initial network
    network = net()

    net.load_network(network, filename='topology.json')
    
    # Visualize the network before PDC removal
    print("Network before PDC removal:")
    net.visualize_network(network)  # Visualize before removal
    
    # Remove a random PDC
    ip = net.remove_random_pdc(network)
    find_ciritical_pmus = network.find_critical_pmus()  # Identify critical PMUs
    print(f"Critical PMUs after PDC removal: {find_ciritical_pmus}")
    
    # Visualize the network after PDC removal
    print("Network after PDC removal:")
    net.visualize_network(network)  # Visualize after removal
    
    # Call the decentralized routing method to fix connections
    net.connect(network, ip)
    
    # Visualize the fixed network
    print("Network after fixing decentralized routing:")
    net.visualize_network(network)  # Visualize after re-routing

if __name__ == "__main__":
    main()