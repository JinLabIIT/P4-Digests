#!/usr/bin/env python3
import socket
import argparse
import sys
import json
import csv
import os

def load_config(config_file):
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at '{config_file}'", file=sys.stderr)
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{config_file}'", file=sys.stderr)
        return None

def pdc_recv(listen_ip, listen_port, csv_file):
    file_exists = os.path.isfile(csv_file)
    if not file_exists:
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['busID', 'voltage', 'phaseAngle', 'timestamp'])

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((listen_ip, listen_port))
    server_socket.listen(5)
    print(f"PDC server '{socket.gethostname()}' listening on {listen_ip}:{listen_port}, logging to {csv_file}")

    try:
        while True:
            client_socket, addr = server_socket.accept()
            print(f"Accepted connection from {addr}")
            handle_connection(client_socket, csv_file)
    except KeyboardInterrupt:
        print("\nPDC server stopped by user.")
    except Exception as e:
        print(f"A server error occurred: {e}", file=sys.stderr)
    finally:
        server_socket.close()

def handle_connection(client_socket, csv_file):
    peer_address = client_socket.getpeername()

    with client_socket, open(csv_file, 'a', newline='') as f:
        writer = csv.writer(f)
        buffer = ""
        while True:
            data = client_socket.recv(1024)
            if not data:
                break  # Connection closed by client
            buffer += data.decode('utf-8')
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                parsed = parse_pmu_message(line)
                if parsed:
                    writer.writerow(parsed)
                    print(f"Stored data: {parsed}")
    
    print(f"Connection from {peer_address} closed.")


def parse_pmu_message(message):
    try:
        parts = message.strip().split()
        busID = parts[1]
        voltage = float(parts[3])
        phaseAngle = float(parts[5])
        timestamp = float(parts[7])
        return [busID, voltage, phaseAngle, timestamp]
    except (IndexError, ValueError) as e:
        # print(f"Failed to parse message: '{message}'. Error: {e}", file=sys.stderr)
        return None
    
def get_mininet_nodename_by_dns():
    """
    Discovers the Mininet node name by performing a reverse DNS lookup on its own IP.
    This is the most reliable discovery method when Mininet is using its internal DNS.
    """
    # Use a trick to get the host's primary IP address
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip_address = s.getsockname()[0]
    except Exception:
        return None
    finally:
        s.close()

    # Perform a reverse DNS lookup to get the hostname
    try:
        # gethostbyaddr() returns a tuple: (hostname, aliaslist, ipaddrlist)
        hostname, _, _ = socket.gethostbyaddr(ip_address)
        # Often, the result is a fully qualified domain name like 'pdc1.mininet.'.
        # We just want the first part.
        return hostname.split('.')[0]
    except socket.herror:
        # This happens if the reverse lookup fails
        return None

if __name__ == "__main__":
    config = load_config('pdc_config.json')
    if config is None:
        sys.exit(1)

    
    parser = argparse.ArgumentParser(description="PDC Server. Must be launched with --name.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    parser.add_argument('--name',
                        type=str,
                        required=True,
                        help="The unique name of this node (e.g., 'pdc1'). Used to get settings from pdc_config.json.")
    
    args, _ = parser.parse_known_args()
    hostname = args.name

    host_config = config.get(hostname, config.get('default', {}))

    parser.add_argument('--ip', 
                        type=str, 
                        default=host_config.get('listen_ip'),
                        help=f"IP address to listen on. (default for this host: {host_config.get('listen_ip')})")
    
    parser.add_argument('--port', 
                        type=int, 
                        default=host_config.get('listen_port'),
                        help=f"Port to listen on. (default for this host: {host_config.get('listen_port')})")
    
    parser.add_argument('--csv', 
                        type=str, 
                        default=host_config.get('csv_file'),
                        help=f"CSV file to store received data. (default for this host: {host_config.get('csv_file')})")

    args = parser.parse_args()

    if not all([args.name, args.ip, args.port, args.csv]):
        print("Error: A required setting (name, ip, port, or csv) is missing.", file=sys.stderr)
        sys.exit(1)

    pdc_recv(args.ip, args.port, args.csv)