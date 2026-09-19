"""Generates a small, clearly-labeled SYNTHETIC network-flow dataset.

This exists purely so the application can be exercised end-to-end (upload ->
preprocess -> train -> predict) without first hunting down a multi-gigabyte
real-world capture. The class-conditional distributions below are made up
for demonstration purposes and do not represent measurements of real attacks.
Every dataset produced by this module is stored with is_demo=True and every
UI surface must show a "Demo / Synthetic data" badge when displaying it.
"""

import numpy as np
import pandas as pd

RNG_SEED = 42

# (label, weight, generator) — generator maps a size to a dict of column -> array
CLASS_PROFILES = ["BENIGN", "DoS", "PortScan", "DDoS", "BruteForce"]


def _flow(rng: np.random.Generator, n: int, *, dur, fwd, bwd, byte_rate, pkt_rate, pkt_len, syn, ack, port_choices):
    return pd.DataFrame(
        {
            "Destination Port": rng.choice(port_choices, size=n),
            "Flow Duration": np.clip(rng.normal(dur, dur * 0.35, n), 1, None),
            "Total Fwd Packets": np.clip(rng.poisson(fwd, n), 0, None),
            "Total Backward Packets": np.clip(rng.poisson(bwd, n), 0, None),
            "Flow Bytes/s": np.clip(rng.normal(byte_rate, byte_rate * 0.4, n), 0, None),
            "Flow Packets/s": np.clip(rng.normal(pkt_rate, pkt_rate * 0.4, n), 0, None),
            "Packet Length Mean": np.clip(rng.normal(pkt_len, pkt_len * 0.3, n), 0, None),
            "SYN Flag Count": rng.poisson(syn, n),
            "ACK Flag Count": rng.poisson(ack, n),
            "Protocol": rng.choice(["TCP", "UDP", "ICMP"], size=n, p=[0.7, 0.25, 0.05]),
        }
    )


def generate_demo_dataset(n_per_class: int = 400, seed: int = RNG_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    frames = []

    frames.append(
        _flow(rng, n_per_class, dur=500_000, fwd=8, bwd=8, byte_rate=2_000, pkt_rate=15, pkt_len=350, syn=1, ack=6, port_choices=[80, 443, 22, 53, 8080]).assign(Label="BENIGN")
    )
    frames.append(
        _flow(rng, n_per_class, dur=50_000, fwd=200, bwd=2, byte_rate=90_000, pkt_rate=400, pkt_len=60, syn=150, ack=2, port_choices=[80, 443]).assign(Label="DoS")
    )
    frames.append(
        _flow(rng, n_per_class, dur=2_000, fwd=1, bwd=0, byte_rate=500, pkt_rate=5, pkt_len=40, syn=1, ack=0, port_choices=list(range(1, 1024))).assign(Label="PortScan")
    )
    frames.append(
        _flow(rng, n_per_class, dur=30_000, fwd=500, bwd=1, byte_rate=250_000, pkt_rate=900, pkt_len=70, syn=400, ack=1, port_choices=[80, 443, 53]).assign(Label="DDoS")
    )
    frames.append(
        _flow(rng, n_per_class, dur=100_000, fwd=40, bwd=40, byte_rate=3_000, pkt_rate=20, pkt_len=100, syn=5, ack=35, port_choices=[22, 21, 3389]).assign(Label="BruteForce")
    )

    df = pd.concat(frames, ignore_index=True)
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    return df
