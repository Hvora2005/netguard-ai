from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ml.predictor import predict_single
from app.models.traffic_flow import TrafficFlow
from app.network.feature_mapping import flows_to_feature_frame
from app.services.prediction_service import load_model_bundle
from app.utils.errors import AppError


def list_flows(
    db: Session,
    *,
    predicted_class: str | None = None,
    protocol: str | None = None,
    severity: str | None = None,
    src_ip: str | None = None,
    dst_ip: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    page: int = 1,
    page_size: int = 25,
) -> dict:
    query = select(TrafficFlow)
    if predicted_class:
        query = query.where(TrafficFlow.predicted_class == predicted_class)
    if protocol:
        query = query.where(TrafficFlow.protocol == protocol)
    if severity:
        query = query.where(TrafficFlow.severity == severity)
    if src_ip:
        query = query.where(TrafficFlow.src_ip == src_ip)
    if dst_ip:
        query = query.where(TrafficFlow.dst_ip == dst_ip)
    if start:
        query = query.where(TrafficFlow.created_at >= start)
    if end:
        query = query.where(TrafficFlow.created_at <= end)

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()

    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    items = (
        db.execute(
            query.order_by(TrafficFlow.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
        .scalars()
        .all()
    )

    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_flow_or_404(db: Session, flow_id: int) -> TrafficFlow:
    flow = db.get(TrafficFlow, flow_id)
    if flow is None:
        raise AppError(f"Traffic flow {flow_id} was not found.", status_code=404)
    return flow


def get_flow_with_explanation(db: Session, flow_id: int) -> dict:
    flow = get_flow_or_404(db, flow_id)

    explanation = None
    explanation_method = None
    if flow.model_id is not None:
        model = flow.model
        if model is not None:
            bundle = load_model_bundle(model)
            raw_flow = {
                "dst_port": flow.dst_port,
                "duration_seconds": flow.duration_seconds,
                "packet_count": flow.packet_count,
                "byte_count": flow.byte_count,
                "byte_rate": flow.byte_rate,
                "packet_rate": flow.packet_rate,
                "syn_count": flow.syn_count,
                "ack_count": flow.ack_count,
                "protocol": flow.protocol,
            }
            features_df = flows_to_feature_frame([raw_flow], bundle.feature_columns)
            result = predict_single(bundle, features_df.iloc[0].to_dict())
            explanation = result["explanation"]
            explanation_method = result["explanation_method"]

    return {
        **{c.name: getattr(flow, c.name) for c in flow.__table__.columns},
        "explanation": explanation,
        "explanation_method": explanation_method,
    }
