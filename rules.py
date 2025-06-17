s1_rules = [
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.1.1", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:01:01", "port": 3}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.1.2", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:01:02", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.1.3", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:01:03", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.1.4", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:01:04", "port": 4}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.1", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:01", "port": 5}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.2", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:02", "port": 6}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.3", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:03", "port": 7}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.4", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:04", "port": 8}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.5", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:05", "port": 9}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.6", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:06", "port": 10}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.7", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:07", "port": 11}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.8", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:08", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.9", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:09", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.10", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:0A", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.11", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:0B", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.12", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:0C", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.13", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:0D", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.14", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:0E", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.15", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:0F", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.16", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:10", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.17", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:11", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.18", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:12", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.19", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:13", "port": 2}
    }
]
s2_rules = [
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.1.1", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:01:01", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.1.2", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:01:02", "port": 3}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.1.3", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:01:03", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.1.4", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:01:04", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.1", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:01", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.2", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:02", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.3", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:03", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.4", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:04", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.5", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:05", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.6", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:06", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.7", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:07", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.8", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:08", "port": 4}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.9", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:09", "port": 5}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.10", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:0A", "port": 6}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.11", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:0B", "port": 7}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.12", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:0C", "port": 8}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.13", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:0D", "port": 9}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.14", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:0E", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.15", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:0F", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.16", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:10", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.17", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:11", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.18", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:12", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.19", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:13", "port": 2}
    }
]
s3_rules = [
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.1.1", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:01:01", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.1.2", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:01:02", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.1.3", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:01:03", "port": 3}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.1.4", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:01:04", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.1", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:01", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.2", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:02", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.3", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:03", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.4", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:04", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.5", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:05", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.6", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:06", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.7", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:07", "port": 1}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.8", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:08", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.9", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:09", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.10", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:0A", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.11", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:0B", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.12", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:0C", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.13", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:0D", "port": 2}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.14", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:0E", "port": 4}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.15", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:0F", "port": 5}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.16", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:10", "port": 6}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.17", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:11", "port": 7}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.18", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:12", "port": 8}
    },
    {
        "table": "MyIngress.ipv4_lpm",
        "match": {"hdr.ipv4.dstAddr": ("10.0.2.19", 32)},
        "action_name": "MyIngress.ipv4_forward",
        "action_params": {"dstAddr": "08:00:00:00:02:13", "port": 9}
    }
]
