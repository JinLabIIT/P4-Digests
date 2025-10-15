#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import argparse
import os
import sys
from time import sleep
import logging
from queue import Queue
from threading import Thread
from scapy.all import Ether, IP, Raw, sendp, Packet, BitField
import ipaddress
import datetime, time
from google.protobuf.json_format import MessageToDict
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
import p4runtime_lib.switch as switch
from p4runtime_lib.switch import ShutdownAllSwitchConnections
from p4.v1 import p4runtime_pb2
from scapy.all import Ether, IP, sendp, raw
import socket

#debugging
def printGrpcError(e):
    print("gRPC Error:", e.details(), end=' ')
    status_code = e.code()
    print("(%s)" % status_code.name, end=' ')
    traceback = sys.exc_info()[2]
    print("[%s:%d]" % (traceback.tb_frame.f_code.co_filename, traceback.tb_lineno))

logging.basicConfig(
    filename='/home/p4/SelfHealingPMU/logs/s1_controller.log',  #This is my static path. You should change it if you're not me.
    level=logging.INFO,         # Log level (INFO, DEBUG, etc.)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

class NetHdr(Packet):
    name = "net_hdr"
    fields_desc = [
        BitField("disconnected_pmus", 0, 7),
        BitField("ip_value", 0, 32),
        BitField("rtype", 0, 1)
    ]

from p4.v1 import p4runtime_pb2

def build_packet_out(p4info_helper, pkt_bytes, egress_port):
    packet_out = p4runtime_pb2.PacketOut()
    packet_out.payload = pkt_bytes

    md = packet_out.metadata.add()
    #md.metadata_id = p4info_helper.get_packet_metadata_id("egress_port")
    md.metadata_id = 1
    md.value = (egress_port).to_bytes(2, "big")

    request = p4runtime_pb2.StreamMessageRequest()
    request.packet.CopyFrom(packet_out)
    return request

def init_prebuilt_packets(p4info_helper):
    prebuilt = {}

    base_eth = Ether(dst="ff:ff:ff:ff:ff:ff", src="00:00:00:00:01:01")
    base_ip  = IP(src="10.0.0.1", proto=253)

    # Example packets (fill in all your finite NetHdr variations)
    # packet_specs = [
    #     # key, ip.dst, NetHdr fields, egress_port
    #     (("to-2", "request-1B"), "10.0.0.2", dict(disconnected_pmus=0x03, ip_value=0x0A000104, rtype=0), 1),
    #     (("to-2", "request-1"), "10.0.0.2", dict(disconnected_pmus=0x04, ip_value=0x0A000101, rtype=0), 1),
    #     (("to-3", "request-1B"), "10.0.0.3", dict(disconnected_pmus=0x03, ip_value=0x0A000104, rtype=0), 2),
    #     (("to-3", "request-1"), "10.0.0.3", dict(disconnected_pmus=0x04, ip_value=0x0A000101, rtype=0), 2),
    #     (("to-2", "return-1B"), "10.0.0.2", dict(disconnected_pmus=0x0A, ip_value=0x0A000104, rtype=1), 1),
    #     (("to-2", "return-1"), "10.0.0.2", dict(disconnected_pmus=0x09, ip_value=0x0A000101, rtype=1), 1),
    #     (("to-3", "return-1B"), "10.0.0.3", dict(disconnected_pmus=0x0A, ip_value=0x0A000104, rtype=1), 2),
    #     (("to-3", "return-1"), "10.0.0.3", dict(disconnected_pmus=0x09, ip_value=0x0A000101, rtype=1), 2),
    # ]

    # for key, dst_ip, nh_fields, egress_port in packet_specs:
    #     ip_layer = IP(src=base_ip.src, proto=base_ip.proto, dst=dst_ip)
    #     pkt = base_eth / ip_layer / NetHdr(**nh_fields)
    #     pkt_bytes = raw(pkt)
    #     pkt_bytes = raw(pkt)
    #     if len(pkt_bytes) < 64: #BMv2 minimum size
    #         pkt_bytes += b'\x00' * (64 - len(pkt_bytes)) 
    #     prebuilt[key] = build_packet_out(p4info_helper, pkt_bytes, egress_port)

    packet_specs = [
        (("to-2", "request-1"), "10.0.0.2", 1),
        (("to-3", "request-1"), "10.0.0.3", 2),
    ]

    for key, dst_ip, egress_port in packet_specs:
        ip_layer = IP(src=base_ip.src, proto=base_ip.proto, dst=dst_ip)
        pkt = Ether(dst="ff:ff:ff:ff:ff:ff", src="00:00:00:00:01:01", type=0x0800) / \
        IP(src="10.0.0.1", dst="10.0.0.2", proto=253) / \
        NetHdr(disconnected_pmus=3, ip_value=0x0A000104, rtype=0)
        pkt_bytes = raw(pkt)
        prebuilt[key] = build_packet_out(p4info_helper, pkt_bytes, egress_port)

    return prebuilt

PDCs_up = [1,1,1,1]
processed_ips = set()

def handle_digests(p4info_helper, switch_conn):

    print(f"Listening for digests on {switch_conn.name}...")
    while True: 
        try:
            digest = switch_conn.dispatcher.digest_queue.get()
            arrival_time = datetime.datetime.now()
            #print("\n----- Digest Received on S1-----")
            #print(digest)

            ts_ns = digest.timestamp  # nanoseconds since switch start
            ts_sec = ts_ns / 1e9
            real_time = datetime.datetime.fromtimestamp(ts_sec)
            
            print("s1:", real_time)
            
            process__digest(switch_conn, digest, p4info_helper, arrival_time) 

            # Acknowledge the digest
            ack = p4runtime_pb2.StreamMessageRequest()
            ack.digest_ack.digest_id = digest.digest_id
            ack.digest_ack.list_id = digest.list_id
            switch_conn.requests_stream.put(ack)
            #print("--- Sent Digest ACK ---\n")

        except grpc.RpcError:
            print(f"gRPC Error. Disconnected from {switch_conn.name}.")
            return
        except Exception as e:
            print(f"An error occurred in handle_digests for {switch_conn.name}: {e}")
            return


def process__digest(s1, digest_t, p4info_helper, arrival_time): #digest_t is incoming digest, digest is after removing it from P4StructLike object
    #global PREBUILT_PKTS
    pkt2 = Ether(dst="ff:ff:ff:ff:ff:ff", src="00:00:00:00:01:01") / \
    IP(src="10.0.0.1", dst="10.0.0.3", proto=253) / \
    NetHdr(disconnected_pmus=0x04, ip_value=0x0A000101, rtype=0)

    pkt1 = Ether(dst="ff:ff:ff:ff:ff:ff", src="00:00:00:00:01:01") / \
    IP(src="10.0.0.1", dst="10.0.0.2", proto=253) / \
    NetHdr(disconnected_pmus=0x04, ip_value=0x0A000101, rtype=0)

    pkt3 = Ether(dst="ff:ff:ff:ff:ff:ff", src="00:00:00:00:01:01") / \
    IP(src="10.0.0.1", dst="10.0.0.3", proto=253) / \
    NetHdr(disconnected_pmus=0x03, ip_value=0x0A000104, rtype=0)

    pkt4 = Ether(dst="ff:ff:ff:ff:ff:ff", src="00:00:00:00:01:01") / \
    IP(src="10.0.0.1", dst="10.0.0.2", proto=253) / \
    NetHdr(disconnected_pmus=0x03, ip_value=0x0A000104, rtype=0)

    digest = digest_t.data[0] # P4Data object
    members = digest.struct.members
    disconnected_pmus = int.from_bytes(members[0].bitstring, 'big')
    ip_value = int.from_bytes(members[1].bitstring, 'big')
    rtype = int.from_bytes(members[2].bitstring, 'big')

    orig_ip = ip_value  # Keep original IP for deduplication

    if orig_ip in processed_ips:
        return

    if(ip_value == 0x0A000101 and rtype == 0):
        disconnected_pmus = 0x04
        ip_value = 0x0A000101  # 10.0.1.1 as int
        rtype = 0
        PDCs_up[0] = 0

        if(PDCs_up[3] == 1):
            
            try:
                table_entry = p4info_helper.buildTableEntry(
                    table_name="MyIngress.ipv4_lpm",
                    match_fields={"hdr.ipv4.dstAddr": ("10.0.1.1", 32)},
                    action_name="MyIngress.ipv4_nat_forward",
                    action_params={
                        "dstAddr": "08:00:00:00:01:04",
                        "port": 4,
                        "new_dst_ip": "10.0.1.4"
                    }
                )
                s1.ModifyTableEntry(table_entry)

                before_install = datetime.datetime.now()

                latency = (before_install - arrival_time).total_seconds() * 1000
                print(f"Installed Rule (latency: {latency:.3f} ms)")

            except grpc.RpcError as e:
                printGrpcError(e)

                for item in e.trailing_metadata():
                    if item[0] == "p4-runtime-error-bin":
                        error = p4runtime_pb2.Error()
                        error.ParseFromString(item[1])
                        print("\n--- P4Runtime Error Report ---")
                        print(error)
                        break

            print("Installed Rule from PDC 1 to PDC 1B")

        else:
            # Send out on the correct interface (replace 'eth0' with your interface)
            sendp(pkt1, iface="s1-eth1", verbose=True)
    
            # Send out on the correct interface (replace 'eth0' with your interface)
            sendp(pkt2, iface="s1-eth2", verbose=True)


    if(ip_value ==  0x0A000104 and rtype == 0):
        disconnected_pmus = 0x03
        ip_value = 0x0A000104 # 10.0.1.4 as int
        rtype = 0
        PDCs_up[3] = 0

        if(PDCs_up[0] == 1):
            try:
                table_entry = p4info_helper.buildTableEntry(
                    table_name="MyIngress.ipv4_lpm",
                    match_fields={"hdr.ipv4.dstAddr": ("10.0.1.4", 32)},
                    action_name="MyIngress.ipv4_nat_forward",
                    action_params={
                        "dstAddr": "08:00:00:00:01:01",
                        "port": 4,
                        "new_dst_ip": "10.0.1.1"
                    }
                )
                s1.ModifyTableEntry(table_entry)

                before_install = datetime.datetime.now()

                latency = (before_install - arrival_time).total_seconds() * 1000
                print(f"Installed Rule (latency: {latency:.3f} ms)")

            except grpc.RpcError as e:
                printGrpcError(e)

                for item in e.trailing_metadata():
                    if item[0] == "p4-runtime-error-bin":
                        error = p4runtime_pb2.Error()
                        error.ParseFromString(item[1])
                        print("\n--- P4Runtime Error Report ---")
                        print(error)
                        break

            print("Installed Rule from PDC 1B to PDC 1")

        else:
            # Send out on the correct interface (replace 'eth0' with your interface)
            sendp(pkt3, iface="s1-eth1", verbose=True)
            # Send out on the correct interface (replace 'eth0' with your interface)
            sendp(pkt4, iface="s1-eth2", verbose=True)

        processed_ips.add(ip_value)

    if(ip_value == 0x0A000102 and rtype == 1):
        disconnected_pmus = 0x06
        ip_value = 0x0A000102  
        rtype = 1

        try:
            if(PDCs_up[0] == 0):
                table_entry = p4info_helper.buildTableEntry(
                    table_name="MyIngress.ipv4_lpm",
                    match_fields={"hdr.ipv4.dstAddr": ("10.0.1.1", 32)},
                    action_name="MyIngress.ipv4_nat_forward",
                    action_params={
                        "dstAddr": "08:00:00:00:01:02",
                        "port": 1,
                        "new_dst_ip": "10.0.1.2"
                    }
                )
                s1.ModifyTableEntry(table_entry)
                print("Installed Rule from PDC 1 to PDC 2")
            if(PDCs_up[3] == 0):
                table_entry = p4info_helper.buildTableEntry(
                    table_name="MyIngress.ipv4_lpm",
                    match_fields={"hdr.ipv4.dstAddr": ("10.0.1.4", 32)},
                    action_name="MyIngress.ipv4_nat_forward",
                    action_params={
                        "dstAddr": "08:00:00:00:01:02",
                        "port": 1,
                        "new_dst_ip": "10.0.1.2"
                    }
                )
                s1.ModifyTableEntry(table_entry)
                print("Installed Rule from PDC 1B to PDC 2")

        except grpc.RpcError as e:
                printGrpcError(e)

                for item in e.trailing_metadata():
                    if item[0] == "p4-runtime-error-bin":
                        error = p4runtime_pb2.Error()
                        error.ParseFromString(item[1])
                        print("\n--- P4Runtime Error Report ---")
                        print(error)
                        break

    if(ip_value == 0x0A000102 and rtype == 0):
        disconnected_pmus = 0x06
        if(PDCs_up[0] == 1):
            ip_value = 0x0A000101
        elif (PDCs_up[3] == 1):
            ip_value = 0x0A000104
        rtype = 1
        PDCs_up[1] = 0

        # Build packet
        pkt = Ether(dst="ff:ff:ff:ff:ff:ff", src="00:00:00:00:01:01") / \
            IP(src="10.0.0.1", dst="10.0.0.2", proto=253) / \
            NetHdr(disconnected_pmus=disconnected_pmus, ip_value=ip_value, rtype=rtype)
    

        # Send out on the correct interface (replace 'eth0' with your interface)
        sendp(pkt, iface="s1-eth1", verbose=True)


    if(ip_value == 0x0A000103 and rtype == 1):
        disconnected_pmus = 0x06
        ip_value = 0x0A000103  
        rtype = 1
        PDCs_up[2] = 0

        try:
            if(PDCs_up[0] == 0):
                table_entry = p4info_helper.buildTableEntry(
                    table_name="MyIngress.ipv4_lpm",
                    match_fields={"hdr.ipv4.dstAddr": ("10.0.1.1", 32)},
                    action_name="MyIngress.ipv4_nat_forward",
                    action_params={
                        "dstAddr": "08:00:00:00:01:03",
                        "port": 2,
                        "new_dst_ip": "10.0.1.3"
                    }
                )
                s1.ModifyTableEntry(table_entry)
                print("Installed Rule from PDC 1 to PDC 3")
            if(PDCs_up[3] == 0):
                table_entry = p4info_helper.buildTableEntry(
                    table_name="MyIngress.ipv4_lpm",
                    match_fields={"hdr.ipv4.dstAddr": ("10.0.1.4", 32)},
                    action_name="MyIngress.ipv4_nat_forward",
                    action_params={
                        "dstAddr": "08:00:00:00:01:03",
                        "port": 2,
                        "new_dst_ip": "10.0.1.3"
                    }
                )
                s1.ModifyTableEntry(table_entry)
                print("Installed Rule from PDC 1B to PDC 3")

        except grpc.RpcError as e:
                printGrpcError(e)

                for item in e.trailing_metadata():
                    if item[0] == "p4-runtime-error-bin":
                        error = p4runtime_pb2.Error()
                        error.ParseFromString(item[1])
                        print("\n--- P4Runtime Error Report ---")
                        print(error)
                        break

    if(ip_value == 0x0A000103 and rtype == 0):
        disconnected_pmus = 0x06
        if(PDCs_up[0] == 1):
            ip_value = 0x0A000101
        elif (PDCs_up[3] == 1):
            ip_value = 0x0A000104
        rtype = 1
        PDCs_up[1] = 0

        # Build packet
        pkt = Ether(dst="ff:ff:ff:ff:ff:ff", src="00:00:00:00:01:01") / \
            IP(src="10.0.0.1", dst="10.0.0.3", proto=253) / \
            NetHdr(disconnected_pmus=disconnected_pmus, ip_value=ip_value, rtype=rtype)
    

        # Send out on the correct interface (replace 'eth0' with your interface)
        sendp(pkt, iface="s1-eth2", verbose=True)



    processed_ips.add(orig_ip)

def main(p4info_file_path, bmv2_file_path):
    # Instantiate a P4Runtime helper from the p4info file
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)

    # for cpm in p4info_helper.p4info.controller_packet_metadata:
    #     print("Controller packet metadata header:", cpm.preamble.name)
    #     for md in cpm.metadata:
    #         print(f"  field: {md.name}, id={md.id}, bitwidth={md.bitwidth}")

    # global PREBUILT_PKTS
    # PREBUILT_PKTS = init_prebuilt_packets(p4info_helper)

    try:
        # Create switch connection object
        s1 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s1',
            address='127.0.0.1:50051',
            device_id=0,
            proto_dump_file='/home/p4/SelfHealingPMU/logs/s1-p4runtime-requests.txt')

        # Establish master arbitration
        s1.MasterArbitrationUpdate(election_id=(0, 1))

        # Install the P4 program on all switches
        s1.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
                                       bmv2_json_file_path=bmv2_file_path)
        print("Installed P4 Program using SetForwardingPipelineConfig on s1")

        # Install rules on each switch
        rt.writeRules(p4info_helper, s1, rules.s1_rules)

        print("Installed rules on s1.")

        # print("metadata id")
        # print(p4info_helper.get_packet_metadata_id("egress_port"))

        request = p4runtime_pb2.WriteRequest()
        request.device_id = s1.device_id
        request.election_id.high = 0
        request.election_id.low = 1
        update = request.updates.add()
        update.type = p4runtime_pb2.Update.INSERT
        digest_entry = update.entity.digest_entry
        digest_entry.digest_id = p4info_helper.get_digests_id("net_report_t")
        digest_entry.config.max_timeout_ns = 0
        digest_entry.config.max_list_size = 1

        print("Registering for digest 'net_report_t'...")
        s1.client_stub.Write(request)
        print("Successfully registered for digest.")

        digest_thread = Thread(target=handle_digests, args=(p4info_helper, s1))
        digest_thread.daemon = True # Allows main program to exit even if thread is running
        digest_thread.start()

        # print(f"SwitchConnection info for {s1.name}:")
        # print(f"  gRPC address: {s1.address}")
        # print(f"  device_id: {s1.device_id}")
        # print(f"  channel target: {s1.channel}")

        while True:
            sleep(1)


    except KeyboardInterrupt:
        print(" Shutting down.")
    except grpc.RpcError as e:
        printGrpcError(e)

    ShutdownAllSwitchConnections()

#I'm using my static paths again here, so you'll need to update them.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime Controller')
    parser.add_argument('--p4info', help='p4info proto in text format from p4c',
                        type=str, action="store", required=False,
                        default='/home/p4/SelfHealingPMU/build/basic.p4.p4info.txtpb')
    parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',
                        type=str, action="store", required=False,
                        default='/home/p4/SelfHealingPMU/build/basic.json')
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
