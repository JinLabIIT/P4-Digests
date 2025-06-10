import sys
import grpc
sys.path.append('/home/p4/tutorials/utils')
import p4runtime_lib.bmv2
import p4runtime_lib.helper
import p4runtime_lib.switch
from p4.v1 import p4runtime_pb2


#debugging
def printGrpcError(e):
    print("gRPC Error:", e.details(), end=' ')
    status_code = e.code()
    print("(%s)" % status_code.name, end=' ')
    traceback = sys.exc_info()[2]
    print("[%s:%d]" % (traceback.tb_frame.f_code.co_filename, traceback.tb_lineno))

def readRules(p4info_helper, sw):
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

def modifyRules(p4info_helper, switch, rules):
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

def writeRules(p4info_helper, switch, rules):
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

def packet_out(p4info_helper, switch, packet):
    egress_port = 2
    packetout = p4info_helper.buildPacketOut(
        payload = packet,
        metadata = {
            1: egress_port.to_bytes(2, byteorder='big')
        }
    )
    switch.PacketOut(packetout)



# Pre-construct the base packet as a byte array
def create_pdc_request_packet(p4info_helper):
    """
    Creates a base Ethernet/IP packet as a byte array.
    """
    base_packet = b'\x08\x00\x00\x00\x01\x11'  # Ethernet src (08:00:00:00:01:11)
    base_packet += b'\x08\x00\x00\x00\x02\x22'  # Ethernet dst (08:00:00:00:02:22)
    base_packet += b'\x08\x00'  # EtherType (IPv4)
    base_packet += b'\x45\x00\x00\x3c\x00\x00\x40\x00\x40\x11\xb7\xe6'  # IPv4 header
    base_packet += b'\x0a\x00\x01\x01'  # IPv4 src (10.0.1.1)
    base_packet += b'\x0a\x00\x02\x02'  # IPv4 dst (10.0.2.2)
    base_packet += b'available_pdc_request'  # Payload

    #base_packet = p4info_helper.buildPacketOut(base_packet, {2: ("\100\000").encode()})

    return base_packet

def modify_packet(base_packet, new_dst_ip, new_dst_mac):
    """
    Modifies the destination IP and MAC address in the base packet.

    :param base_packet: The pre-constructed base packet (bytes).
    :param new_dst_ip: The new destination IP address (string, e.g., "10.0.3.3").
    :param new_dst_mac: The new destination MAC address (string, e.g., "08:00:00:00:03:33").
    :return: The modified packet (bytes).
    """
    # Convert IP and MAC to bytes
    dst_ip_bytes = bytes(map(int, new_dst_ip.split('.')))
    dst_mac_bytes = bytes(int(x, 16) for x in new_dst_mac.split(':'))

    # Replace the destination MAC (bytes 0-5) and destination IP (bytes 30-33)
    modified_packet = bytearray(base_packet)
    modified_packet[0:6] = dst_mac_bytes
    modified_packet[30:34] = dst_ip_bytes

    return bytes(modified_packet)