#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
import argparse
import os
import sys
from time import sleep
import logging

import grpc

# Import P4Runtime lib from parent utils dir
# Probably there's a better way of doing this.
# this is my local path to the utils folder
# you should change it to your own path
sys.path.append('/home/p4/tutorials/utils')
import p4runtime_lib.bmv2
import p4runtime_lib.helper
from p4runtime_lib.switch import ShutdownAllSwitchConnections

SWITCH_TO_HOST_PORT = 1
SWITCH_TO_SWITCH_PORT = 2


def writeIngressRules(p4info_helper, ingress_sw, dst_eth_addr, dst_ip_addr, out_port):
    """
    Installs forwarding rules in the ipv4_lpm table to forward packets based on destination IP.

    :param p4info_helper: the P4Info helper
    :param ingress_sw: the ingress switch connection
    :param dst_eth_addr: the destination MAC address to write in the action
    :param dst_ip_addr: the destination IP address to match in the table
    :param out_port: the output port to forward the packet
    """
    logging.info(f"Installing forwarding rule on {ingress_sw.name} for destination IP {dst_ip_addr}")

    # Build the table entry for the ipv4_lpm table
    table_entry = p4info_helper.buildTableEntry(
        table_name="MyIngress.ipv4_lpm",  # Table name in the P4 program
        match_fields={
            "hdr.ipv4.dstAddr": (dst_ip_addr, 32)  # Match the destination IP address
        },
        action_name="MyIngress.ipv4_forward",  # Action name in the P4 program
        action_params={
            "dstAddr": dst_eth_addr,  # Set the destination MAC address
            "port": out_port          # Set the output port
        })

    # Write the table entry to the switch
    try:
        ingress_sw.WriteTableEntry(table_entry)
        print(f"Installed forwarding rule on {ingress_sw.name} for destination IP {dst_ip_addr}")
    except grpc.RpcError as e:
        printGrpcError(e)


#this is for helping us to read the table rules - do not worry about it
def readTableRules(p4info_helper, sw):
    """
    Reads the table entries from all tables on the switch.

    :param p4info_helper: the P4Info helper
    :param sw: the switch connection
    """
    print('\n----- Reading tables rules for %s -----' % sw.name)
    for response in sw.ReadTableEntries():
        for entity in response.entities:
            entry = entity.table_entry
            table_name = p4info_helper.get_tables_name(entry.table_id)
            print('%s: ' % table_name, end=' ')
            for m in entry.match:
                print(p4info_helper.get_match_field_name(table_name, m.field_id), end=' ')
                print('%r' % (p4info_helper.get_match_field_value(m),), end=' ')
            action = entry.action.action
            action_name = p4info_helper.get_actions_name(action.action_id)
            print('->', action_name, end=' ')
            for p in action.params:
                print(p4info_helper.get_action_param_name(action_name, p.param_id), end=' ')
                print('%r' % p.value, end=' ')
            print()


def printCounter(p4info_helper, sw, counter_name, index):
    """
    Reads the specified counter at the specified index from the switch. In our
    program, the index is the tunnel ID. If the index is 0, it will return all
    values from the counter.

    :param p4info_helper: the P4Info helper
    :param sw:  the switch connection
    :param counter_name: the name of the counter from the P4 program
    :param index: the counter index (in our case, the tunnel ID)
    """
    for response in sw.ReadCounters(p4info_helper.get_counters_id(counter_name), index):
        for entity in response.entities:
            counter = entity.counter_entry
            print("%s %s %d: %d packets (%d bytes)" % (
                sw.name, counter_name, index,
                counter.data.packet_count, counter.data.byte_count
                       ))

#debugging
def printGrpcError(e):
    print("gRPC Error:", e.details(), end=' ')
    status_code = e.code()
    print("(%s)" % status_code.name, end=' ')
    traceback = sys.exc_info()[2]
    print("[%s:%d]" % (traceback.tb_frame.f_code.co_filename, traceback.tb_lineno))


def writeNewRules(p4info_helper, switch, rules):
    """
    Updates the rules on the specified switch.

    :param p4info_helper: The P4Info helper object.
    :param switch: The switch connection object.
    :param rules: A list of rules to install on the switch.
    """
    print(f"Updating rules on {switch.name}...")

    try:
        print(f"Modifying existing rules on {switch.name}...")
        for rule in rules:
            table_name = rule["table"]
            match_fields = rule["match"]
            action_name = rule["action_name"]
            action_params = rule["action_params"]

            # Build the updated table entry
            table_entry = p4info_helper.buildTableEntry(
                table_name=table_name,
                match_fields=match_fields,
                action_name=action_name,
                action_params=action_params
            )

            # Use ModifyTableEntry to update the table entry
            switch.ModifyTableEntry(table_entry)
            print(f"Modified rule on {switch.name}: {match_fields} -> {action_name} {action_params}")
    except grpc.RpcError as e:
        printGrpcError(e)


logging.basicConfig(
    filename='controller.log',  # Log file name
    level=logging.INFO,         # Log level (INFO, DEBUG, etc.)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)


def writeStaticRules(p4info_helper, switch, rules):
    """
    Installs static rules on a switch based on the provided rules.

    :param p4info_helper: The P4Info helper object.
    :param switch: The switch connection object.
    :param rules: A list of rules to install on the switch.
    """
    for rule in rules:
        table_name = rule["table"]
        match_fields = rule.get("match", {})
        action_name = rule["action_name"]
        action_params = rule.get("action_params", {})

        # Build the table entry
        table_entry = p4info_helper.buildTableEntry(
            table_name=table_name,
            match_fields=match_fields,
            action_name=action_name,
            action_params=action_params
        )

        # Write the table entry to the switch
        try:
            switch.WriteTableEntry(table_entry)
            print(f"Installed rule on {switch.name}: {match_fields} -> {action_name} {action_params}")
        except grpc.RpcError as e:
            printGrpcError(e)


def main(p4info_file_path, bmv2_file_path):
    # Instantiate a P4Runtime helper from the p4info file
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)

    try:
        # Create switch connection objects for s1, s2, and s3
        s1 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s1',
            address='127.0.0.1:50051',
            device_id=0,
            proto_dump_file='logs/s1-p4runtime-requests.txt')
        s2 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s2',
            address='127.0.0.1:50052',
            device_id=1,
            proto_dump_file='logs/s2-p4runtime-requests.txt')
        s3 = p4runtime_lib.bmv2.Bmv2SwitchConnection(
            name='s3',
            address='127.0.0.1:50053',
            device_id=2,
            proto_dump_file='logs/s3-p4runtime-requests.txt')

        # Establish master arbitration
        s1.MasterArbitrationUpdate()
        s2.MasterArbitrationUpdate()
        s3.MasterArbitrationUpdate()

        # Install the P4 program on all switches
        s1.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
                                       bmv2_json_file_path=bmv2_file_path)
        print("Installed P4 Program using SetForwardingPipelineConfig on s1")
        s2.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
                                       bmv2_json_file_path=bmv2_file_path)
        print("Installed P4 Program using SetForwardingPipelineConfig on s2")
        s3.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
                                       bmv2_json_file_path=bmv2_file_path)
        print("Installed P4 Program using SetForwardingPipelineConfig on s3")

        print("Installed P4 Program on all switches.")

        # Define rules for each switch
        s1_rules = [
            {
                "table": "MyIngress.ipv4_lpm",
                "match": {"hdr.ipv4.dstAddr": ("10.0.1.1", 32)},
                "action_name": "MyIngress.ipv4_forward",
                "action_params": {"dstAddr": "08:00:00:00:01:11", "port": 1}
            },
            {
                "table": "MyIngress.ipv4_lpm",
                "match": {"hdr.ipv4.dstAddr": ("10.0.2.2", 32)},
                "action_name": "MyIngress.ipv4_forward",
                "action_params": {"dstAddr": "08:00:00:00:02:22", "port": 2}
            },
            {
                "table": "MyIngress.ipv4_lpm",
                "match": {"hdr.ipv4.dstAddr": ("10.0.3.3", 32)},
                "action_name": "MyIngress.ipv4_forward",
                "action_params": {"dstAddr": "08:00:00:00:03:33", "port": 3}
            }
        ]

        s2_rules = [
            {
                "table": "MyIngress.ipv4_lpm",
                "match": {"hdr.ipv4.dstAddr": ("10.0.1.1", 32)},
                "action_name": "MyIngress.ipv4_forward",
                "action_params": {"dstAddr": "08:00:00:00:01:11", "port": 2}
            },
            {
                "table": "MyIngress.ipv4_lpm",
                "match": {"hdr.ipv4.dstAddr": ("10.0.2.2", 32)},
                "action_name": "MyIngress.ipv4_forward",
                "action_params": {"dstAddr": "08:00:00:00:02:22", "port": 1}
            },
            {
                "table": "MyIngress.ipv4_lpm",
                "match": {"hdr.ipv4.dstAddr": ("10.0.3.3", 32)},
                "action_name": "MyIngress.ipv4_forward",
                "action_params": {"dstAddr": "08:00:00:00:03:00", "port": 3}
            }
        ]

        s3_rules = [
            {
                "table": "MyIngress.ipv4_lpm",
                "match": {"hdr.ipv4.dstAddr": ("10.0.1.1", 32)},
                "action_name": "MyIngress.ipv4_forward",
                "action_params": {"dstAddr": "08:00:00:00:01:11", "port": 2}
            },
            {
                "table": "MyIngress.ipv4_lpm",
                "match": {"hdr.ipv4.dstAddr": ("10.0.2.2", 32)},
                "action_name": "MyIngress.ipv4_forward",
                "action_params": {"dstAddr": "08:00:00:00:02:22", "port": 3}
            },
            {
                "table": "MyIngress.ipv4_lpm",
                "match": {"hdr.ipv4.dstAddr": ("10.0.3.3", 32)},
                "action_name": "MyIngress.ipv4_forward",
                "action_params": {"dstAddr": "08:00:00:00:03:33", "port": 1}
            }
        ]

        # Install rules on each switch
        writeStaticRules(p4info_helper, s1, s1_rules)
        writeStaticRules(p4info_helper, s2, s2_rules)
        writeStaticRules(p4info_helper, s3, s3_rules)

        print("Installed static rules on all switches.")

        #overwrite the rules with updated rules
        s1_rules = [
            {
                "table": "MyIngress.ipv4_lpm",
                "match": {"hdr.ipv4.dstAddr": ("10.0.1.1", 32)},
                "action_name": "MyIngress.ipv4_forward",
                "action_params": {"dstAddr": "08:00:00:00:01:11", "port": 1}
            },
            {
                "table": "MyIngress.ipv4_lpm",
                "match": {"hdr.ipv4.dstAddr": ("10.0.2.2", 32)},
                "action_name": "MyIngress.ipv4_forward",
                "action_params": {"dstAddr": "08:00:00:00:03:33", "port": 3}
            },
            {
                "table": "MyIngress.ipv4_lpm",
                "match": {"hdr.ipv4.dstAddr": ("10.0.3.3", 32)},
                "action_name": "MyIngress.ipv4_forward",
                "action_params": {"dstAddr": "08:00:00:00:03:33", "port": 3}
            }
        ]

        s2_rules = [
            {
                "table": "MyIngress.ipv4_lpm",
                "match": {"hdr.ipv4.dstAddr": ("10.0.1.1", 32)},
                "action_name": "MyIngress.ipv4_forward",
                "action_params": {"dstAddr": "08:00:00:00:01:11", "port": 2}
            },
            {
                "table": "MyIngress.ipv4_lpm",
                "match": {"hdr.ipv4.dstAddr": ("10.0.2.2", 32)},
                "action_name": "MyIngress.ipv4_forward",
                "action_params": {"dstAddr": "08:00:00:00:03:33", "port": 3}
            },
            {
                "table": "MyIngress.ipv4_lpm",
                "match": {"hdr.ipv4.dstAddr": ("10.0.3.3", 32)},
                "action_name": "MyIngress.ipv4_forward",
                "action_params": {"dstAddr": "08:00:00:00:03:33", "port": 3}
            }
        ]

        s3_rules = [
            {
                "table": "MyIngress.ipv4_lpm",
                "match": {"hdr.ipv4.dstAddr": ("10.0.1.1", 32)},
                "action_name": "MyIngress.ipv4_forward",
                "action_params": {"dstAddr": "08:00:00:00:01:11", "port": 2}
            },
            {
                "table": "MyIngress.ipv4_lpm",
                "match": {"hdr.ipv4.dstAddr": ("10.0.2.2", 32)},
                "action_name": "MyIngress.ipv4_forward",
                "action_params": {"dstAddr": "08:00:00:00:03:33", "port": 1}
            },
            {
                "table": "MyIngress.ipv4_lpm",
                "match": {"hdr.ipv4.dstAddr": ("10.0.3.3", 32)},
                "action_name": "MyIngress.ipv4_forward",
                "action_params": {"dstAddr": "08:00:00:00:03:33", "port": 1}
            }
        ]

        s1_arp_rules = [
            {
                "table": "MyIngress.arp_table",
                "match": {"hdr.arp.tpa": ("10.0.3.3")},
                "action_name": "MyIngress.send_arp_reply",
                "action_params": {"target_mac": "08:00:00:00:03:33", "target_ip": "10.0.3.3"}
            }
        ]

        elapsed_time = 0
        updated = False
        # This is what will end up being triggered by the digest stuff
        while True:
            sleep(1)
            if not updated:
                elapsed_time += 1
                print(f"Elapsed time: {elapsed_time} seconds")

            # Simulate ping success (replace with actual check)
            if check_ping_success():  # Replace with your ping check logic
                elapsed_time = 0
                print("Ping from h1 to h2 succeeded!")
                break

            if elapsed_time > 4:
                print("Ping from h1 to h2 failed. Updating rules...")
                writeNewRules(p4info_helper, s1, s1_rules)
                writeNewRules(p4info_helper, s2, s2_rules)
                writeNewRules(p4info_helper, s3, s3_rules)
                #writeStaticRules(p4info_helper, s1, s1_arp_rules)
                updated = True
                elapsed_time = 0
                readTableRules(p4info_helper, s1)
                readTableRules(p4info_helper, s2)
                readTableRules(p4info_helper, s3)

    except KeyboardInterrupt:
        print(" Shutting down.")
    except grpc.RpcError as e:
        printGrpcError(e)

    ShutdownAllSwitchConnections()


def check_ping_success():    
    # This will be a notif from the control plan when the PDC connection times out
    return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime Controller')
    parser.add_argument('--p4info', help='p4info proto in text format from p4c',
                        type=str, action="store", required=False,
                        default='./build/basic.p4.p4info.txtpb')
    parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',
                        type=str, action="store", required=False,
                        default='./build/basic.json')
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
