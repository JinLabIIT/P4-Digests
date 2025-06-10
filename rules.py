# Rules for switch s1
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
    # {
    #     "table": "MyIngress.ipv4_lpm",
    #     "match": {"hdr.ipv4.dstAddr": ("10.0.3.3", 32)},
    #     "action_name": "MyIngress.ipv4_forward",
    #     "action_params": {"dstAddr": "08:00:00:00:03:33", "port": 3}
    # }
    #{
    #    "table": "MyIngress.check_switch_source_ip",
    #    "match": {"hdr.ipv4.srcAddr": ("10.0.0.0", 24)},
    #    "action_name": "MyIngress.mark_as_switch_traffic"
    #}
]

# Rules for switch s2
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
        "action_params": {"dstAddr": "08:00:00:00:03:33", "port": 3}
    }
]

# Rules for switch s3
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

#updated switch rules
s1_update = [
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

s2_update = [
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

s3_update = [
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
        "match": {"hdr.arp.tpa": "10.0.2.2"},
        "action_name": "MyIngress.send_arp_reply",
        "action_params": {"target_mac": "08:00:00:00:03:33", "target_ip": "10.0.2.2"}
    }
]