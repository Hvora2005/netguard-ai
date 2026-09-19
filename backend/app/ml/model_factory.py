from app.utils.errors import AppError

SUPPORTED_MODELS = [
    "logistic_regression",
    "decision_tree",
    "random_forest",
    "svm",
    "knn",
    "xgboost",
    "mlp",
]


def build_estimator(model_type: str, hyperparameters: dict, class_weight: dict | None, random_state: int):
    hyperparameters = hyperparameters or {}

    if model_type == "logistic_regression":
        from sklearn.linear_model import LogisticRegression

        return LogisticRegression(
            max_iter=hyperparameters.get("max_iter", 1000),
            C=hyperparameters.get("C", 1.0),
            class_weight=class_weight,
            random_state=random_state,
        )

    if model_type == "decision_tree":
        from sklearn.tree import DecisionTreeClassifier

        return DecisionTreeClassifier(
            max_depth=hyperparameters.get("max_depth"),
            min_samples_split=hyperparameters.get("min_samples_split", 2),
            class_weight=class_weight,
            random_state=random_state,
        )

    if model_type == "random_forest":
        from sklearn.ensemble import RandomForestClassifier

        return RandomForestClassifier(
            n_estimators=hyperparameters.get("n_estimators", 200),
            max_depth=hyperparameters.get("max_depth"),
            class_weight=class_weight,
            random_state=random_state,
            n_jobs=-1,
        )

    if model_type == "svm":
        from sklearn.svm import SVC

        return SVC(
            C=hyperparameters.get("C", 1.0),
            kernel=hyperparameters.get("kernel", "rbf"),
            probability=True,
            class_weight=class_weight,
            random_state=random_state,
        )

    if model_type == "knn":
        from sklearn.neighbors import KNeighborsClassifier

        return KNeighborsClassifier(
            n_neighbors=hyperparameters.get("n_neighbors", 5),
        )

    if model_type == "xgboost":
        from xgboost import XGBClassifier

        return XGBClassifier(
            n_estimators=hyperparameters.get("n_estimators", 200),
            max_depth=hyperparameters.get("max_depth", 6),
            learning_rate=hyperparameters.get("learning_rate", 0.1),
            eval_metric="mlogloss",
            random_state=random_state,
            n_jobs=-1,
        )

    if model_type == "mlp":
        from sklearn.neural_network import MLPClassifier

        return MLPClassifier(
            hidden_layer_sizes=tuple(hyperparameters.get("hidden_layer_sizes", [64, 32])),
            max_iter=hyperparameters.get("max_iter", 300),
            random_state=random_state,
        )

    raise AppError(f"Unsupported model_type '{model_type}'. Supported: {', '.join(SUPPORTED_MODELS)}")


def supports_class_weight(model_type: str) -> bool:
    return model_type in {"logistic_regression", "decision_tree", "random_forest", "svm"}
