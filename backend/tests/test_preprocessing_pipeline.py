from app.preprocessing.pipeline import build_preprocessor, resolve_labels, split_feature_types
from app.schemas.preprocessing import PreprocessingConfig
from app.services.demo_data import generate_demo_dataset


def test_preprocessor_fit_on_train_only_avoids_leakage():
    df = generate_demo_dataset(n_per_class=50)
    config = PreprocessingConfig(task_type="multiclass")
    feature_columns = [c for c in df.columns if c != "Label"]

    numeric_cols, categorical_cols = split_feature_types(df, feature_columns)
    assert "Protocol" in categorical_cols
    assert "Flow Duration" in numeric_cols

    preprocessor = build_preprocessor(config, numeric_cols, categorical_cols)
    train = df.iloc[:150]
    test = df.iloc[150:]

    train_transformed = preprocessor.fit_transform(train[feature_columns])
    test_transformed = preprocessor.transform(test[feature_columns])

    assert train_transformed.shape[1] == test_transformed.shape[1]
    assert train_transformed.shape[0] == len(train)
    assert test_transformed.shape[0] == len(test)


def test_binary_label_mapping_collapses_attack_classes():
    df = generate_demo_dataset(n_per_class=20)
    config = PreprocessingConfig(task_type="binary", benign_labels=["BENIGN"])
    mapped = resolve_labels(df["Label"], config)
    assert set(mapped.unique()) == {"BENIGN", "MALICIOUS"}
