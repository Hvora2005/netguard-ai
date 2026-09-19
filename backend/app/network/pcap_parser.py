"""Parses an uploaded .pcap/.pcapng file into per-flow statistics using Scapy.

Reading a capture file offline does not require Npcap/WinPcap (those are only
needed for LIVE packet capture on Windows), so this works out of the box.

Flows are grouped by the unidirectional 5-tuple (src_ip, dst_ip, src_port,
dst_port, protocol) — i.e. each direction of a conversation is its own flow
row here, rather than reconstructing full bidirectional forward/backward
flows the way a tool like CICFlowMeter does. This is a deliberate
simplification: it is practical to implement without extra system
dependencies and still yields real, non-fabricated per-flow statistics; it
means a "Total Backward Packets"-style field cannot be derived from this
parser and is reported as 0 when features are later mapped to a model's
expected columns (see app/services/pcap_service.py).
"""

from collections import defaultdict
from pathlib import Path

from app.utils.errors import AppError

try:
    from scapy.all import IP, TCP, UDP, rdpcap

    SCAPY_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only when scapy isn't installed
    SCAPY_AVAILABLE = False


def _protocol_name(packet) -> str:
    if packet.haslayer(TCP):
        return "TCP"
    if packet.haslayer(UDP):
        return "UDP"
    if packet.haslayer("ICMP"):
        return "ICMP"
    return "OTHER"


def parse_pcap_to_flows(file_path: Path) -> list[dict]:
    if not SCAPY_AVAILABLE:
        raise AppError(
            "PCAP parsing requires the 'scapy' package, which is a normal pip dependency "
            "(no extra system install needed to read capture files). It appears to be missing "
            "from this environment — reinstall backend requirements and try again.",
            status_code=500,
        )

    try:
        packets = rdpcap(str(file_path))
    except Exception as exc:
        raise AppError(f"Could not parse this capture file: {exc}") from exc

    if len(packets) == 0:
        raise AppError("The uploaded capture file contains no packets.")

    flows: dict[tuple, dict] = defaultdict(lambda: {
        "packet_count": 0,
        "byte_count": 0,
        "syn_count": 0,
        "ack_count": 0,
        "timestamps": [],
    })

    for packet in packets:
        if not packet.haslayer(IP):
            continue

        ip_layer = packet[IP]
        protocol = _protocol_name(packet)
        src_port = dst_port = None
        if packet.haslayer(TCP):
            src_port, dst_port = int(packet[TCP].sport), int(packet[TCP].dport)
        elif packet.haslayer(UDP):
            src_port, dst_port = int(packet[UDP].sport), int(packet[UDP].dport)

        key = (ip_layer.src, ip_layer.dst, src_port, dst_port, protocol)
        flow = flows[key]
        flow["packet_count"] += 1
        flow["byte_count"] += len(packet)
        flow["timestamps"].append(float(packet.time))

        if packet.haslayer(TCP):
            flags = packet[TCP].flags
            if flags & 0x02:  # SYN
                flow["syn_count"] += 1
            if flags & 0x10:  # ACK
                flow["ack_count"] += 1

    results = []
    for (src_ip, dst_ip, src_port, dst_port, protocol), flow in flows.items():
        timestamps = flow["timestamps"]
        first_seen, last_seen = min(timestamps), max(timestamps)
        duration = max(last_seen - first_seen, 1e-6)
        results.append(
            {
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": src_port,
                "dst_port": dst_port,
                "protocol": protocol,
                "packet_count": flow["packet_count"],
                "byte_count": flow["byte_count"],
                "duration_seconds": duration,
                "packet_rate": flow["packet_count"] / duration,
                "byte_rate": flow["byte_count"] / duration,
                "syn_count": flow["syn_count"],
                "ack_count": flow["ack_count"],
                "first_seen": first_seen,
                "last_seen": last_seen,
            }
        )

    return results
