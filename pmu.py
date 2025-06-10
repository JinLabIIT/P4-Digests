from scapy.all import IP, TCP, send
import time

def generate_tcp_packets(dst_ip, dst_port, interval=1):
    """
    Continuously generates and sends TCP packets to the specified destination.

    :param dst_ip: Destination IP address (e.g., h2's IP).
    :param dst_port: Destination port (e.g., 80).
    :param interval: Time interval between packets (in seconds).
    """
    print(f"Starting to send TCP packets to {dst_ip}:{dst_port} every {interval} second(s)...")
    try:
        while True:
            # Create an IP/TCP packet
            packet = IP(dst=dst_ip) / TCP(dport=dst_port, flags="S")
            
            # Send the packet
            send(packet, verbose=False)
            print(f"Sent TCP SYN packet to {dst_ip}:{dst_port}")
            
            # Wait for the specified interval
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped sending packets.")

if __name__ == "__main__":
    # Destination IP and port (h2's IP and a chosen port)
    destination_ip = "10.0.2.2"  # h2's IP address
    destination_port = 80        # Destination port (e.g., HTTP port)
    packet_interval = 1          # Interval between packets (in seconds)

    # Start generating packets
    generate_tcp_packets(destination_ip, destination_port, packet_interval)