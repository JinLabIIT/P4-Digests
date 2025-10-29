// SPDX-License-Identifier: Apache-2.0
/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

const bit<9> CPU_PORT = 510;

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

header udp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<16> length;
    bit<16> checksum;
}

@controller_header("packet_out")
header packet_out_header_t {
    bit<9> egress_port;
    bit<7> i_need_seven_bits;
}

struct headers {
    ethernet_t ethernet;
    ipv4_t ipv4;
    udp_t udp;
    packet_out_header_t packet_out;
    arp_t arp;
}

struct digest_report_t {
    bit<32> srcIP;
    bit<32> dstIP;
}

struct metadata {
    digest_report_t digest_report;
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
            default: accept;
        }
    }

    state parse_arp {
        packet.extract(hdr.arp);
        transition accept;
    }
}

/*************************************************************************
************ C H E C K S U M   V E R I F I C A T I O N *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}


/*************************************************************************
************** I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    action drop() {
        mark_to_drop(standard_metadata);
    }

    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    action ipv4_nat_forward(macAddr_t dstAddr, egressSpec_t port, ip4Addr_t new_dst_ip) {
        standard_metadata.egress_spec = port;                                             
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
        hdr.ipv4.dstAddr = new_dst_ip;
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

    action send_digest() {
        if (hdr.ipv4.isValid()) { //This line is used to set the condition to trigger the digest message.
            digest<digest_report_t>(1, {hdr.ipv4.srcAddr, hdr.ipv4.dstAddr}); //This line sends the digest. digest<report_type>(1, {report_field_1, report_field_2, ...}); 
        } 
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            ipv4_forward;
            ipv4_nat_forward;
            send_digest;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }

    apply {
        if (hdr.ipv4.isValid()) {
            ipv4_lpm.apply();
        }
    }
}

/*************************************************************************
**************** E G R E S S   P R O C E S S I N G *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    apply {
    }
}


/*************************************************************************
**************** C H E C K S U M   U P D A T E *******************
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
**************** D E P A R S E R *****************************************
*************************************************************************/
control MyDeparser(packet_out packet,
                   in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.net_hdr); 
        packet.emit(hdr.arp);  
    }
} 

/*************************************************************************
*********************** S W I T C H  ************************************
*************************************************************************/

V1Switch(
    MyParser(),
    MyVerifyChecksum(),
    MyIngress(),
    MyEgress(),
    MyComputeChecksum(),
    MyDeparser()
) main;

