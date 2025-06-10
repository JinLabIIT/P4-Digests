#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import argparse
import os
import sys
from time import sleep
import logging
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root) 
import rules
import runtime_functions as rt
from switch_functions import Network as net


import grpc

# Import P4Runtime lib from parent utils dir
# Probably there's a better way of doing this.
# this is my local path to the utils folder
# you should change it to your own path
sys.path.append('/home/p4/tutorials/utils')
import p4runtime_lib.bmv2
import p4runtime_lib.helper
from p4runtime_lib.switch import ShutdownAllSwitchConnections
from p4.v1 import p4runtime_pb2
from scapy.all import Ether, IP, sendp
import socket

#debugging
def printGrpcError(e):
    print("gRPC Error:", e.details(), end=' ')
    status_code = e.code()
    print("(%s)" % status_code.name, end=' ')
    traceback = sys.exc_info()[2]
    print("[%s:%d]" % (traceback.tb_frame.f_code.co_filename, traceback.tb_lineno))

logging.basicConfig(
    filename='../logs/s1_controller.log',  # Log file name
    level=logging.INFO,         # Log level (INFO, DEBUG, etc.)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

def phase_I():
    # Set up the initial network
    network = net()

    net.load_network(network, filename='../topology.json')
    
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

def read_stream(p4info_helper, stream_channel):
    def request_iterator():
        while True:
            yield p4runtime_pb2.StreamMessageRequest() # Explicitly yield an empty request

    try:
        response_iterator = stream_channel(request_iterator())
        while True:
            try:
                response = next(response_iterator)
                print("Received response from stream channel.")
                handle_stream_message(p4info_helper, response)
            except grpc.RpcError as e:
                print("gRPC Error in response iteration:")
                printGrpcError(e)
                break
            except StopIteration:
                print("Stream closed by the server (response iterator).")
                break
            except Exception as e:
                print(f"An unexpected error occurred during response iteration: {e}")
                break
    except grpc.RpcError as e:
        print("gRPC Error during stream initiation:")
        printGrpcError(e)
    except Exception as e:
        print(f"An unexpected error occurred during stream initiation: {e}")

def handle_stream_message(p4info_helper, stream_msg):
    for update in stream_msg.updates:
        if update.HasField('digest'):
            digest = update.digest
            digest_name = p4info_helper.get_digest_name(digest.digest_id)
            if digest_name == "SwitchTrafficDigest":
                print("Received SwitchTrafficDigest from switch:", digest.device_id)
                digest_data = p4runtime_pb2.DigestData()
                for data in digest.data:
                    digest_data.ParseFromString(data)
                    dst_eth = digest_data.struct.members[0].bitstring.hex()
                    src_ip_int = int.from_bytes(digest_data.struct.members[1].bitstring, byteorder='big')
                    src_ip = socket.inet_ntoa(src_ip_int.to_bytes(4, 'big'))
                    dst_ip_int = int.from_bytes(digest_data.struct.members[2].bitstring, byteorder='big')
                    dst_ip = socket.inet_ntoa(dst_ip_int.to_bytes(4, 'big'))
                    payload_bytes = digest_data.struct.members[3].byte_string
                    payload_hex = payload_bytes.hex()
                    payload_decoded = payload_bytes.decode('utf-8', errors='ignore') # Try to decode as UTF-8

                    print(f"  Destination MAC: {dst_eth}")
                    print(f"  Source IP: {src_ip}")
                    print(f"  Destination IP: {dst_ip}")
                    print(f"  Payload (Hex): {payload_hex}")
                    print(f"  Payload (Decoded): {payload_decoded}")

def make_packet(src_ip, dst_ip, src_mac, dst_mac, payload):
    ether_layer = Ether(src=src_mac, dst=dst_mac)
    ip_layer = IP(version=4, src=src_ip, dst=dst_ip, proto=253)
    packet = ether_layer / ip_layer / payload
    return packet

def process__digest(digest,pdcs):
    source_ip = digest.digest_entry[0].entity
    src_mac = digest.digest_entry[0].src_mac
    payload = digest.digest_entry[0].payload

    if(payload == b"Available PDC Request" and source_ip == '10.0.0.2'):
        packet = make_packet('10.0.0.1', source_ip, '00:00:00:00:01:11', src_mac, pdcs[0].encode)
        output_port = "s1-eth2"
        sendp(packet, iface=output_port, verbose=False)
        print(f"Sent packet out of interface '{output_port}' on s1 using Scapy.")
    elif(payload == b"Available PDC Request" and source_ip == '10.0.0.3'):
        packet = make_packet('10.0.0.', source_ip, '00:00:00:00:01:11', src_mac, pdcs[0].encode)
        output_port = "s1-eth3"
        sendp(packet, iface=output_port, verbose=False)
        print(f"Sent packet out of interface '{output_port}' on s1 using Scapy.")
    elif(source_ip == '10.0.0.1'):
        packet = make_packet('10.0.0.1', source_ip, '00:00:00:00:01:11', src_mac, pdcs[0].encode)
        output_port = "s1-eth2"
        sendp(packet, iface=output_port, verbose=False)
        print(f"Sent packet out of interface '{output_port}' on s1 using Scapy.")


def main(p4info_file_path, bmv2_file_path):
    # Instantiate a P4Runtime helper from the p4info file
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)

    try:
        # Create switch connection object
        s1 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s1',
            address='127.0.0.1:50052',
            device_id=1,
            proto_dump_file='../logs/s1-p4runtime-requests.txt')

        # Establish master arbitration
        s1.MasterArbitrationUpdate()

        channel = s1.channel

        stream_channel = channel.stream_stream(
            '/p4.v1.P4Runtime/StreamChannel',
            request_serializer=p4runtime_pb2.StreamMessageRequest.SerializeToString,
            response_deserializer=p4runtime_pb2.StreamMessageResponse.FromString,
        )
        s1.StreamChannel = stream_channel


        # Install the P4 program on all switches
        s1.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
                                       bmv2_json_file_path=bmv2_file_path)
        print("Installed P4 Program using SetForwardingPipelineConfig on s1")

        # Install rules on each switch
        rt.writeRules(p4info_helper, s1, rules.s1_rules)

        print("Installed rules on s1.")

        read_stream(p4info_helper, stream_channel) 

        # This is what will end up being triggered by the digest stuff
        while True:
            sleep(1)
            print("main loop")

    except KeyboardInterrupt:
        print(" Shutting down.")
    except grpc.RpcError as e:
        printGrpcError(e)

    ShutdownAllSwitchConnections()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime Controller')
    parser.add_argument('--p4info', help='p4info proto in text format from p4c',
                        type=str, action="store", required=False,
                        default='../build/basic.p4.p4info.txtpb')
    parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',
                        type=str, action="store", required=False,
                        default='../build/basic.json')
    args = parser.parse_args()

    if not os.path.exists(args.p4info):
        parser.print_help()
        print("\np4info file not found: %s\nHave you run 'make'?" % args.p4info)
        parser.exit(1)
    if not os.path.exists(args.bmv2_json):
        parser.print_help()
        print("\nBMv2 JSON file not found: %s\nHave you run 'make'?" % args.bmv2_json)
        parser.exit(1)
    main(args.p4info, args.bmv2_json)
