from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.severity import resolve_severity
from app.ml.predictor import predict_batch
from app.models.ml_model import MLModel
from app.models.security_alert import SecurityAlert
from app.models.traffic_flow import TrafficFlow
from app.network.feature_mapping import flows_to_feature_frame
from app.network.pcap_parser import parse_pcap_to_flows
from app.services.prediction_service import load_model_bundle
from app.utils.errors import AppError
from app.utils.files import sanitize_filename, unique_stored_name

ALLOWED_EXTENSIONS = {".pcap", ".pcapng"}


def save_pcap_upload(original_filename: str, content: bytes) -> Path:
    suffix = Path(original_filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise AppError("Only .pcap and .pcapng files are supported.")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise AppError(f"File exceeds the {settings.max_upload_size_mb}MB upload limit.")

    upload_dir = settings.resolve_path(settings.upload_path)
    stored_name = unique_stored_name(sanitize_filename(original_filename))
    file_path = upload_dir / stored_name
    file_path.write_bytes(content)
    return file_path


def analyze_pcap(db: Session, file_path: Path, original_filename: str, model: MLModel) -> dict:
    flows = parse_pcap_to_flows(file_path)
    bundle = load_model_bundle(model)

    feature_frame = flows_to_feature_frame(flows, bundle.feature_columns)
    predicted_classes, confidences = predict_batch(bundle, feature_frame)

    saved_flows: list[TrafficFlow] = []
    alerts_created = 0

    for flow, predicted_class, confidence in zip(flows, predicted_classes, confidences, strict=True):
        severity = resolve_severity(predicted_class, confidence)

        flow_row = TrafficFlow(
            source_name=sanitize_filename(original_filename),
            model_id=model.id,
            src_ip=flow["src_ip"],
            dst_ip=flow["dst_ip"],
            src_port=flow["src_port"],
            dst_port=flow["dst_port"],
            protocol=flow["protocol"],
            packet_count=flow["packet_count"],
            byte_count=flow["byte_count"],
            duration_seconds=flow["duration_seconds"],
            packet_rate=flow["packet_rate"],
            byte_rate=flow["byte_rate"],
            syn_count=flow["syn_count"],
            ack_count=flow["ack_count"],
            predicted_class=predicted_class,
            confidence=confidence,
            severity=severity,
            first_seen=datetime.fromtimestamp(flow["first_seen"], tz=timezone.utc),
        )
        db.add(flow_row)
        db.flush()  # assign flow_row.id without committing yet
        saved_flows.append(flow_row)

        if severity != "none":
            db.add(
                SecurityAlert(
                    flow_id=flow_row.id,
                    severity=severity,
                    classification=predicted_class,
                    confidence=confidence,
                    message=f"Model detected traffic matching the learned pattern for {predicted_class}.",
                    source=f"{flow['src_ip']}:{flow['src_port']}" if flow["src_port"] else flow["src_ip"],
                    destination=f"{flow['dst_ip']}:{flow['dst_port']}" if flow["dst_port"] else flow["dst_ip"],
                )
            )
            alerts_created += 1

    db.commit()

    class_counts: dict[str, int] = {}
    for predicted_class in predicted_classes:
        class_counts[predicted_class] = class_counts.get(predicted_class, 0) + 1

    return {
        "flow_count": len(saved_flows),
        "alerts_created": alerts_created,
        "classification_breakdown": class_counts,
        "model_used": model.name,
    }
