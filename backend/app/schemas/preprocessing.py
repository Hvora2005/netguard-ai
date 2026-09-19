from pydantic import BaseModel, Field


class PreprocessingConfig(BaseModel):
    feature_columns: list[str] | None = None  # None => all columns except target
    missing_strategy: str = Field(default="median", pattern="^(mean|median|most_frequent|drop_rows)$")
    scaling: str = Field(default="standard", pattern="^(standard|minmax|none)$")
    categorical_encoding: str = Field(default="onehot", pattern="^(onehot|label)$")
    handle_imbalance: str = Field(default="none", pattern="^(none|smote|class_weight)$")
    test_size: float = Field(default=0.2, ge=0.1, le=0.5)
    task_type: str = Field(default="multiclass", pattern="^(binary|multiclass)$")
    benign_labels: list[str] = Field(default_factory=lambda: ["BENIGN", "Benign", "benign", "0", "Normal"])
    random_state: int = 42


class PreprocessingPreviewRequest(BaseModel):
    dataset_id: int
    config: PreprocessingConfig


class ColumnStat(BaseModel):
    name: str
    mean: float | None = None
    std: float | None = None
    missing_count: int


class PreprocessingPreviewResponse(BaseModel):
    before_row_count: int
    after_row_count: int
    before_class_distribution: dict[str, int]
    after_class_distribution: dict[str, int]
    before_numeric_stats: list[ColumnStat]
    after_numeric_stats: list[ColumnStat]
    numeric_feature_count: int
    categorical_feature_count: int
    notes: list[str]
