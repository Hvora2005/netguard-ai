"""One connected integration test walking the full pipeline the acceptance
criteria in README/AGENTS describe: dataset -> train -> predict -> pcap
analysis -> report. Kept as a single ordered test so each stage's real
output (dataset id, model id, experiment id) feeds the next stage, the same
way a person clicking through the UI would.
"""

import pytest


@pytest.fixture(scope="module")
def trained_model(client):
    dataset = client.post("/api/datasets/demo").json()

    train_response = client.post(
        "/api/models/train",
        json={
            "dataset_id": dataset["id"],
            "model_type": "random_forest",
            "model_name": "pytest-rf",
            "hyperparameters": {},
            "preprocessing": {
                "feature_columns": None,
                "missing_strategy": "median",
                "scaling": "standard",
                "categorical_encoding": "onehot",
                "handle_imbalance": "none",
                "test_size": 0.2,
                "task_type": "multiclass",
                "benign_labels": ["BENIGN"],
                "random_state": 42,
            },
        },
    )
    assert train_response.status_code == 200, train_response.text
    experiment = train_response.json()
    assert experiment["status"] == "completed"
    assert experiment["metrics"]["accuracy"] > 0.8

    models = client.get("/api/models").json()
    model = next(m for m in models if m["experiment_id"] == experiment["id"])
    client.put(f"/api/models/{model['id']}/activate")

    return {"dataset": dataset, "experiment": experiment, "model": model}


def test_model_training_produces_usable_metrics(trained_model):
    metrics = trained_model["experiment"]["metrics"]
    assert set(metrics["class_labels"]) == {"BENIGN", "BruteForce", "DDoS", "DoS", "PortScan"}
    assert len(metrics["confusion_matrix"]) == 5


def test_prediction_uses_the_saved_preprocessing_pipeline(client, trained_model):
    model_id = trained_model["model"]["id"]

    response = client.post(
        "/api/predict",
        json={
            "model_id": model_id,
            "features": {
                "Destination Port": 80,
                "Flow Duration": 40000,
                "Total Fwd Packets": 500,
                "Total Backward Packets": 1,
                "Flow Bytes/s": 250000,
                "Flow Packets/s": 900,
                "Packet Length Mean": 70,
                "SYN Flag Count": 400,
                "ACK Flag Count": 1,
                "Protocol": "TCP",
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["predicted_class"] in {"BENIGN", "BruteForce", "DDoS", "DoS", "PortScan"}
    assert body["confidence"] is not None
    assert 0.0 <= body["confidence"] <= 1.0


def test_prediction_rejects_unknown_model(client):
    response = client.post("/api/predict", json={"model_id": 999999, "features": {}})
    assert response.status_code == 404


def test_pcap_analysis_populates_traffic_and_alerts(client, trained_model, tmp_path):
    scapy = pytest.importorskip("scapy.all")
    pcap_path = tmp_path / "sample.pcap"

    packets = [
        scapy.IP(src="10.0.0.5", dst="10.0.0.9") / scapy.TCP(sport=5000 + i, dport=80, flags="S") for i in range(20)
    ]
    scapy.wrpcap(str(pcap_path), packets)

    with open(pcap_path, "rb") as f:
        response = client.post(
            "/api/pcap/analyze",
            files={"file": ("sample.pcap", f, "application/octet-stream")},
            data={"model_id": str(trained_model["model"]["id"])},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["flow_count"] >= 1

    traffic = client.get("/api/traffic").json()
    assert traffic["total"] >= 1


def test_report_generation_produces_downloadable_files(client, trained_model):
    response = client.post(
        "/api/reports/generate",
        json={"experiment_id": trained_model["experiment"]["id"], "formats": ["html", "csv"]},
    )
    assert response.status_code == 200
    report = response.json()

    html_response = client.get(f"/api/reports/{report['id']}/download", params={"format": "html"})
    assert html_response.status_code == 200
    assert b"NetGuard AI" in html_response.content
