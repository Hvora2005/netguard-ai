import csv
import io
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.experiment import Experiment
from app.models.report import Report
from app.models.security_alert import SecurityAlert
from app.models.traffic_flow import TrafficFlow
from app.services.prediction_service import get_model_global_explanation, load_model_bundle
from app.utils.errors import AppError


def _build_report_content(db: Session, experiment: Experiment) -> dict:
    dataset = experiment.dataset
    model = experiment.model

    feature_importance = None
    if model is not None:
        try:
            explanation = get_model_global_explanation(model)
            feature_importance = explanation.get("importances")
        except Exception:
            feature_importance = None

    traffic_stats = None
    alerts = []
    if model is not None:
        severity_counts = dict(
            db.execute(
                select(TrafficFlow.severity, func.count()).where(TrafficFlow.model_id == model.id).group_by(TrafficFlow.severity)
            ).all()
        )
        flow_total = db.execute(select(func.count()).where(TrafficFlow.model_id == model.id)).scalar_one()
        traffic_stats = {"total_flows": flow_total, "severity_breakdown": severity_counts}

        alert_rows = (
            db.execute(
                select(SecurityAlert)
                .join(TrafficFlow, SecurityAlert.flow_id == TrafficFlow.id)
                .where(TrafficFlow.model_id == model.id)
                .order_by(SecurityAlert.created_at.desc())
                .limit(10)
            )
            .scalars()
            .all()
        )
        alerts = [
            {
                "severity": a.severity,
                "classification": a.classification,
                "confidence": a.confidence,
                "source": a.source,
                "destination": a.destination,
                "status": a.status,
                "created_at": a.created_at.isoformat(),
            }
            for a in alert_rows
        ]

    conclusions = [
        "Metrics reported here reflect performance on this experiment's held-out test split only; "
        "they are not a guarantee of performance on different or future traffic.",
        "No model is claimed to be universally \"best\" — model choice should be driven by which metric "
        "(e.g. recall vs. precision) matters most for the deployment's risk tolerance and by the class distribution.",
        "Predictions describe traffic matching a learned pattern for a given class; they are not confirmed "
        "real-world attacks, and feature-contribution values describe model behavior, not real-world causation.",
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "experiment": {
            "id": experiment.id,
            "model_type": experiment.model_type,
            "task_type": experiment.task_type,
            "status": experiment.status,
            "duration_seconds": experiment.duration_seconds,
            "created_at": experiment.created_at.isoformat(),
        },
        "dataset": {
            "id": dataset.id,
            "filename": dataset.original_filename,
            "n_rows": dataset.n_rows,
            "n_columns": dataset.n_columns,
            "target_column": dataset.target_column,
            "class_distribution": dataset.class_distribution,
            "is_demo": dataset.is_demo,
        },
        "preprocessing_config": experiment.preprocessing_config,
        "model": {"id": model.id, "name": model.name} if model else None,
        "metrics": experiment.metrics,
        "feature_importance": feature_importance,
        "traffic_stats": traffic_stats,
        "alerts": alerts,
        "conclusions": conclusions,
    }


def _render_html(content: dict) -> str:
    metrics = content["metrics"] or {}
    per_class_rows = "".join(
        f"<tr><td>{label}</td><td>{m['precision']:.3f}</td><td>{m['recall']:.3f}</td><td>{m['f1']:.3f}</td><td>{m['support']}</td></tr>"
        for label, m in (metrics.get("per_class") or {}).items()
    )
    class_dist_rows = "".join(
        f"<tr><td>{label}</td><td>{count}</td></tr>" for label, count in (content["dataset"]["class_distribution"] or {}).items()
    )
    importance_rows = "".join(
        f"<tr><td>{item['feature']}</td><td>{item['importance']:.4f}</td></tr>" for item in (content["feature_importance"] or [])
    )
    alert_rows = "".join(
        f"<tr><td>{a['severity']}</td><td>{a['classification']}</td><td>{a['source']}</td><td>{a['destination']}</td><td>{a['status']}</td></tr>"
        for a in content["alerts"]
    )
    conclusions_items = "".join(f"<li>{c}</li>" for c in content["conclusions"])
    demo_badge = " (DEMO / SYNTHETIC DATA)" if content["dataset"]["is_demo"] else ""

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>NetGuard AI Report — Experiment {content['experiment']['id']}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 2rem; color: #111; }}
h1, h2 {{ color: #0f766e; }}
table {{ border-collapse: collapse; margin-bottom: 1.5rem; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; font-size: 13px; }}
th {{ background: #f0fdfa; }}
.badge {{ background: #fef3c7; color: #92400e; padding: 2px 6px; border-radius: 4px; font-size: 12px; }}
</style></head>
<body>
<h1>NetGuard AI — Experiment Report #{content['experiment']['id']}</h1>
<p>Generated {content['generated_at']}</p>

<h2>Dataset{'<span class="badge">DEMO</span>' if content['dataset']['is_demo'] else ''}</h2>
<p>{content['dataset']['filename']}{demo_badge} — {content['dataset']['n_rows']} rows, {content['dataset']['n_columns']} columns, target column "{content['dataset']['target_column']}"</p>
<table><tr><th>Class</th><th>Count</th></tr>{class_dist_rows}</table>

<h2>Model</h2>
<p>{content['experiment']['model_type']} ({content['experiment']['task_type']}), trained in {content['experiment']['duration_seconds']:.2f}s</p>
<h3>Preprocessing configuration</h3>
<pre>{content['preprocessing_config']}</pre>

<h2>Evaluation metrics</h2>
<p>Accuracy: {metrics.get('accuracy', 'N/A')} · Macro F1: {metrics.get('macro_f1', 'N/A')} · Weighted F1: {metrics.get('weighted_f1', 'N/A')} · ROC-AUC: {metrics.get('roc_auc', 'N/A')} · PR-AUC: {metrics.get('pr_auc', 'N/A')}</p>
<table><tr><th>Class</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr>{per_class_rows}</table>

<h2>Feature importance</h2>
<table><tr><th>Feature</th><th>Importance</th></tr>{importance_rows or '<tr><td colspan="2">Not available for this model type.</td></tr>'}</table>

<h2>Traffic statistics ({(content['traffic_stats'] or {}).get('total_flows', 0)} flows classified by this model)</h2>
<pre>{(content['traffic_stats'] or {}).get('severity_breakdown', {})}</pre>

<h2>Recent alerts</h2>
<table><tr><th>Severity</th><th>Classification</th><th>Source</th><th>Destination</th><th>Status</th></tr>{alert_rows or '<tr><td colspan="5">No alerts recorded for this model.</td></tr>'}</table>

<h2>Conclusions</h2>
<ul>{conclusions_items}</ul>
</body></html>"""


def _render_csv(content: dict) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["section", "key", "value"])
    writer.writerow(["experiment", "id", content["experiment"]["id"]])
    writer.writerow(["experiment", "model_type", content["experiment"]["model_type"]])
    writer.writerow(["experiment", "task_type", content["experiment"]["task_type"]])
    metrics = content["metrics"] or {}
    for key in ("accuracy", "macro_f1", "weighted_f1", "roc_auc", "pr_auc"):
        writer.writerow(["metrics", key, metrics.get(key)])
    for label, m in (metrics.get("per_class") or {}).items():
        writer.writerow([f"per_class:{label}", "precision", m["precision"]])
        writer.writerow([f"per_class:{label}", "recall", m["recall"]])
        writer.writerow([f"per_class:{label}", "f1", m["f1"]])
    for label, count in (content["dataset"]["class_distribution"] or {}).items():
        writer.writerow(["class_distribution", label, count])
    for item in content["feature_importance"] or []:
        writer.writerow(["feature_importance", item["feature"], item["importance"]])
    return buffer.getvalue()


def _render_pdf(content: dict) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"NetGuard AI — Experiment Report #{content['experiment']['id']}", styles["Title"]),
        Paragraph(f"Generated {content['generated_at']}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Dataset", styles["Heading2"]),
        Paragraph(
            f"{content['dataset']['filename']} — {content['dataset']['n_rows']} rows, target column "
            f"'{content['dataset']['target_column']}'" + (" [DEMO / SYNTHETIC DATA]" if content["dataset"]["is_demo"] else ""),
            styles["Normal"],
        ),
        Spacer(1, 12),
        Paragraph("Model & metrics", styles["Heading2"]),
        Paragraph(f"{content['experiment']['model_type']} ({content['experiment']['task_type']})", styles["Normal"]),
    ]

    metrics = content["metrics"] or {}
    metrics_table = [["Metric", "Value"]] + [
        [key.replace("_", " ").title(), str(metrics.get(key, "N/A"))] for key in ("accuracy", "macro_f1", "weighted_f1", "roc_auc", "pr_auc")
    ]
    story.append(_styled_table(metrics_table))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Conclusions", styles["Heading2"]))
    for c in content["conclusions"]:
        story.append(Paragraph(f"• {c}", styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()


def _styled_table(data):
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    table = Table(data)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return table


def generate_report(db: Session, experiment: Experiment, formats: list[str]) -> Report:
    if experiment.status != "completed" or not experiment.metrics:
        raise AppError("Reports can only be generated for completed experiments with metrics.")

    content = _build_report_content(db, experiment)
    reports_dir = settings.resolve_path(settings.reports_path)

    report = Report(experiment_id=experiment.id)

    if "html" in formats:
        html_path = reports_dir / f"experiment_{experiment.id}_report.html"
        html_path.write_text(_render_html(content), encoding="utf-8")
        report.html_path = str(html_path)

    if "csv" in formats:
        csv_path = reports_dir / f"experiment_{experiment.id}_report.csv"
        csv_path.write_text(_render_csv(content), encoding="utf-8")
        report.csv_path = str(csv_path)

    if "pdf" in formats:
        pdf_path = reports_dir / f"experiment_{experiment.id}_report.pdf"
        pdf_path.write_bytes(_render_pdf(content))
        report.pdf_path = str(pdf_path)

    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report_or_404(db: Session, report_id: int) -> Report:
    report = db.get(Report, report_id)
    if report is None:
        raise AppError(f"Report {report_id} was not found.", status_code=404)
    return report


def resolve_report_file(report: Report, fmt: str) -> Path:
    path_str = {"html": report.html_path, "csv": report.csv_path, "pdf": report.pdf_path}.get(fmt)
    if not path_str:
        raise AppError(f"This report was not generated in '{fmt}' format.", status_code=404)
    path = Path(path_str)
    if not path.exists():
        raise AppError(f"The report file for format '{fmt}' is missing on disk.", status_code=404)
    return path
