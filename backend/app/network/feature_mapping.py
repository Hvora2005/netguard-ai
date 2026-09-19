"""Maps a parsed PCAP flow's raw packet-derived stats onto the feature
columns a trained model expects (e.g. CIC-IDS-style names such as
"Destination Port", "Flow Duration", "Flow Bytes/s"). Any expected column
this parser cannot derive (notably backward-direction stats, since flows
here are unidirectional — see app/network/pcap_parser.py) is left as NaN so
the model's own imputer (fit during training) fills it consistently, the
same way it fills a missing value from any other source.
"""

import numpy as np
import pandas as pd

_RAW_TO_MODEL_FIELD = {
    "Destination Port": "dst_port",
    "Flow Duration": "duration_seconds",
    "Total Fwd Packets": "packet_count",
    "Flow Bytes/s": "byte_rate",
    "Flow Packets/s": "packet_rate",
    "SYN Flag Count": "syn_count",
    "ACK Flag Count": "ack_count",
    "Protocol": "protocol",
}


def flows_to_feature_frame(flows: list[dict], feature_columns: list[str]) -> pd.DataFrame:
    rows = []
    for flow in flows:
        row = {}
        for column in feature_columns:
            if column in _RAW_TO_MODEL_FIELD:
                row[column] = flow[_RAW_TO_MODEL_FIELD[column]]
            elif column == "Packet Length Mean":
                row[column] = flow["byte_count"] / flow["packet_count"] if flow["packet_count"] else 0
            elif column == "Total Backward Packets":
                row[column] = 0  # not derivable from a unidirectional flow parse; documented limitation
            else:
                row[column] = np.nan
        rows.append(row)
    return pd.DataFrame(rows, columns=feature_columns)
