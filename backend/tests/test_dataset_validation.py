def test_reject_non_csv_upload(client):
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("not_a_csv.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 400
    assert "csv" in response.json()["detail"].lower()


def test_reject_empty_csv(client):
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("empty.csv", b"", "text/csv")},
    )
    assert response.status_code == 400


def test_get_missing_dataset_returns_404(client):
    response = client.get("/api/datasets/999999")
    assert response.status_code == 404


def test_demo_dataset_has_target_column_preselected(client):
    response = client.post("/api/datasets/demo")
    assert response.status_code == 200
    body = response.json()
    assert body["is_demo"] is True
    assert body["target_column"] == "Label"
    assert body["n_rows"] > 0
    assert set(body["class_distribution"].keys()) == {"BENIGN", "DoS", "PortScan", "DDoS", "BruteForce"}
