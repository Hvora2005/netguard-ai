import numpy as np
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.preprocessing import label_binarize


def evaluate_predictions(y_test: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray | None, class_labels: list[str]) -> dict:
    report = classification_report(
        y_test,
        y_pred,
        labels=list(range(len(class_labels))),
        target_names=class_labels,
        output_dict=True,
        zero_division=0,
    )

    cm = confusion_matrix(y_test, y_pred, labels=list(range(len(class_labels))))

    metrics: dict = {
        "accuracy": report["accuracy"],
        "macro_f1": report["macro avg"]["f1-score"],
        "weighted_f1": report["weighted avg"]["f1-score"],
        "per_class": {
            label: {
                "precision": report[label]["precision"],
                "recall": report[label]["recall"],
                "f1": report[label]["f1-score"],
                "support": report[label]["support"],
            }
            for label in class_labels
        },
        "confusion_matrix": cm.tolist(),
        "class_labels": class_labels,
        "roc_auc": None,
        "pr_auc": None,
    }

    if y_proba is None:
        return metrics

    try:
        if len(class_labels) == 2:
            metrics["roc_auc"] = float(roc_auc_score(y_test, y_proba[:, 1]))
            metrics["pr_auc"] = float(average_precision_score(y_test, y_proba[:, 1]))
        else:
            y_bin = label_binarize(y_test, classes=list(range(len(class_labels))))
            metrics["roc_auc"] = float(roc_auc_score(y_bin, y_proba, average="macro", multi_class="ovr"))
            metrics["pr_auc"] = float(average_precision_score(y_bin, y_proba, average="macro"))
    except ValueError:
        # Happens if a class present in class_labels has zero test-set samples; leave AUC as None
        # rather than reporting a misleading number.
        pass

    return metrics
