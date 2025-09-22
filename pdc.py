#!/usr/bin/env python3
import socket
import argparse
import sys
import json
import csv
import os
from scapy.all import Ether, IP, Raw, sendp, Packet, BitField
import ipaddress
import signal

# Turn SIGINT and SIGTERM into KeyboardInterrupt
signal.signal(signal.SIGINT, lambda s, f: (_ for _ in ()).throw(KeyboardInterrupt))
signal.signal(signal.SIGTERM, lambda s, f: (_ for _ in ()).throw(KeyboardInterrupt))

class NetHdr(Packet):
    name = "net_hdr"
    fields_desc = [
        BitField("disconnected_pmus", 0, 7),
        BitField("ip_value", 0, 32),
        BitField("rtype", 0, 1)
    ]

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

def pdc_recv(listen_ip, listen_port, csv_file, pmu_count, mac_address):
    file_exists = os.path.isfile(csv_file)
    if not file_exists:
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['busID', 'voltage', 'phaseAngle', 'timestamp'])

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((listen_ip, listen_port))
    print(f"PDC UDP server '{socket.gethostname()}' listening on {listen_ip}:{listen_port}, logging to {csv_file}")

    try:
        with open(csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            #buffer = ""
            while True:
                data, addr = server_socket.recvfrom(1024)
                buffer = data.decode('utf-8')
                for line in buffer.split('\n'):
                    parsed = parse_pmu_message(line)
                    if parsed:
                        writer.writerow(parsed)
                        print(f"Stored data from {addr}: {parsed}")
    except KeyboardInterrupt:
        disconnected_pmus = pmu_count
        ip_value = int(ipaddress.ip_address(listen_ip))  # 10.0.1.1 as int
        rtype = 0

        pkt = Ether(dst="ff:ff:ff:ff:ff:ff", src=mac_address) / \
              IP(src=listen_ip, dst="10.0.0.1", proto=253) / \
              NetHdr(disconnected_pmus=disconnected_pmus, ip_value=ip_value, rtype=rtype)

        sendp(pkt, iface="eth0", verbose=True)
        print("Sent custom net_hdr packet from PDC.")

        print("\nPDC UDP server stopped by user.")
    except Exception as e:
        print(f"A server error occurred: {e}", file=sys.stderr)
    finally:
        server_socket.close()

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
        hostname, _, _ = socket.gethostbyaddr(ip_address)
        return hostname.split('.')[0]
    except socket.herror:
        return None

if __name__ == "__main__":
    config = load_config('pdc_config.json')
    if config is None:
        sys.exit(1)

    parser = argparse.ArgumentParser(description="PDC Server. Must be launched with --name.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--name', type=str, required=True,
                        help="The unique name of this node (e.g., 'pdc1'). Used to get settings from pdc_config.json.")
    args, _ = parser.parse_known_args()
    hostname = args.name

    host_config = config.get(hostname, config.get('default', {}))

    parser.add_argument('--ip', type=str, default=host_config.get('listen_ip'),
                        help=f"IP address to listen on. (default for this host: {host_config.get('listen_ip')})")
    parser.add_argument('--port', type=int, default=host_config.get('listen_port'),
                        help=f"Port to listen on. (default for this host: {host_config.get('listen_port')})")
    parser.add_argument('--csv', type=str, default=host_config.get('csv_file'),
                        help=f"CSV file to store received data. (default for this host: {host_config.get('csv_file')})")
    parser.add_argument('--pmu', type=int, default=host_config.get('pmu'),
                        help=f"Number of PMUs connected to host at network init. (default for this host: {host_config.get('pmu')})")
    parser.add_argument('--mac', type=str, default=host_config.get('mac'),
                            help=f"Mac Address. (default for this host: {host_config.get('mac')})")
    args = parser.parse_args()

    if not all([args.name, args.ip, args.port, args.csv, args.pmu, args.mac]):
        print("Error: A required setting (name, ip, port, pmu, mac, or csv) is missing.", file=sys.stderr)
        sys.exit(1)

    pdc_recv(args.ip, args.port, args.csv, args.pmu, args.mac)