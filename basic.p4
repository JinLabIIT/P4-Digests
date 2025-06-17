// SPDX-License-Identifier: Apache-2.0
/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_IPV4 = 0x800;

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9> egressSpec_t; 
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16> etherType;
}

header ipv4_t {
    bit<4> version;
    bit<4> ihl;
    bit<8> diffserv;
    bit<16> totalLen;
    bit<16> identification;
    bit<3> flags;
    bit<13> fragOffset;
    bit<8> ttl;
    bit<8> protocol;
    bit<16> hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

header arp_t {
    bit<16> htype;
    bit<16> ptype;
    bit<8> hlen;
    bit<8> plen;
    bit<16> oper;
    macAddr_t sha;
    ip4Addr_t spa;
    macAddr_t tha;
    ip4Addr_t tpa;
}

header net_header_t {
    bit<8> disconnected_pmus;
    bit<32> ip_value;
    bit<8> rtype; //return or request
}

@controller_header("packet_out")
header packet_out_header_t {
    bit egress_port;
}
@controller_header("packet_in")
header packet_in_header_t {
    bit ingress_port;
}

struct headers {
    ethernet_t ethernet;
    ipv4_t ipv4;
    net_header_t net_hdr;
    arp_t arp;
}

struct DigestReport_t {
    bit<48> dst_eth;
    bit<32> src_ip;
    bit<32> dst_ip;
    bit<32> payload;
}

struct metadata {
    egressSpec_t egress_port;  // needed for runtimeAPI packet_out
    DigestReport_t report;    // For digest filtering
}


/*************************************************************************
*********************** P A R S E R   ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            0x0806: parse_arp;  // ARP EtherType
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            253: parse_net_hdr;  // example
            default: accept;
        }
    }

    state parse_net_hdr {
        packet.extract(hdr.net_hdr);
        transition accept;
    }

    state parse_arp {
        packet.extract(hdr.arp);
        transition accept;
    }

}

/*************************************************************************
************ C H E C K S U M     V E R I F I C A T I O N    *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}


/*************************************************************************
************** I N G R E S S    P R O C E S S I N G    *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                    inout metadata meta,
                    inout standard_metadata_t standard_metadata) {

    register<ip4Addr_t>(1) saved_src_ip;

    action drop() {
        mark_to_drop(standard_metadata);
    }

    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    action send_arp_reply(macAddr_t target_mac, ip4Addr_t target_ip) {
        hdr.ethernet.dstAddr = hdr.ethernet.srcAddr;
        hdr.ethernet.srcAddr = target_mac;
        hdr.arp.tha = hdr.arp.sha;
        hdr.arp.tpa = hdr.arp.spa;
        hdr.arp.sha = target_mac;
        hdr.arp.spa = target_ip;
        hdr.arp.oper = 2;  // ARP reply
        standard_metadata.egress_spec = standard_metadata.ingress_port;
    }

    action mark_as_switch_traffic() {
        meta.report.dst_eth = hdr.ethernet.dstAddr;
        meta.report.src_ip = hdr.ipv4.srcAddr;
        meta.report.dst_ip = hdr.ipv4.dstAddr;
        //meta.report.payload = hdr.net_hdr.value; 
        digest(1, meta.report);
    }

    action save_src_ip() {
        saved_src_ip.write(0, hdr.ipv4.srcAddr);
    }

    //action clone_if_request() {
    //    clone(I2E, 99);
    //}

    table check_switch_source_ip {
        key = {
            hdr.ipv4.srcAddr: lpm;
        }
        actions = {
            mark_as_switch_traffic();
            NoAction;
        }
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            ipv4_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }

    table arp_table {
        key = {
            hdr.arp.tpa: exact;
        }
        actions = {
            send_arp_reply;
            NoAction;
        }
        size = 1024;
    }

    //table clone_table {
    //    key = {
    //        hdr.net_hdr.rtype: exact;
    //    }
    //    actions = {
    //        clone_if_request;
    //        NoAction;
    //    }
    //    size = 1;
    //    default_action = NoAction();
    //}

    apply {
        //if (hdr.net_hdr.isValid()) {
        //    clone_table.apply();
        //}   
        if (hdr.arp.isValid()) {
            arp_table.apply();
        } else if (hdr.ipv4.isValid()) {
            ipv4_lpm.apply();
        }
    }

}
/*************************************************************************
**************** E G R E S S    P R O C E S S I N G    *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                    inout metadata meta,
                    inout standard_metadata_t standard_metadata) {

    //action modify_cloned_packet() {
    //    if (hdr.net_hdr.isValid()) {
    //        ip4Addr_t value;
    //        saved_src_ip.read(val, 0);
    //        hdr.ipv4.dstAddr = val;
    //        hdr.net_hdr.ip_value = 0x12345678; // or any logic
    //        hdr.net_hdr.rtype = 1;
    //    }
    //}   
    
    apply {
        //if (standard_metadata.instance_type == PKT_INSTANCE_TYPE_INGRESS_CLONE) {
        //    modify_cloned_packet();
        //}
    }
}

/*************************************************************************
************* C H E C K S U M     C O M P U T A T I O N    *************
*************************************************************************/

control MyComputeChecksum(inout headers  hdr, inout metadata meta) {
        apply {
            update_checksum(
                hdr.ipv4.isValid(),
                { hdr.ipv4.version,
                  hdr.ipv4.ihl,
                  hdr.ipv4.diffserv,
                  hdr.ipv4.totalLen,
                  hdr.ipv4.identification,
                  hdr.ipv4.flags,
                  hdr.ipv4.fragOffset,
                  hdr.ipv4.ttl,
                  hdr.ipv4.protocol,
                  hdr.ipv4.srcAddr,
                  hdr.ipv4.dstAddr },
                hdr.ipv4.hdrChecksum,
                HashAlgorithm.csum16);
        }
}

/*************************************************************************
*********************** D E P A R S E R   ******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        //if (hdr.ipv4.isValid()) {
            packet.emit(hdr.ipv4);
        //}
        //if (hdr.net_hdr.isValid()) {
        //    packet.emit(hdr.net_hdr);
        //}   
        //if (hdr.arp.isValid()) {
        //    packet.emit(hdr.arp);
        //}
    }
}

/*************************************************************************
*********************** S W I T C H    *******************************
*************************************************************************/

V1Switch(
    MyParser(),
    MyVerifyChecksum(),
    MyIngress(),
    MyEgress(),
    MyComputeChecksum(),
    MyDeparser()
) main;