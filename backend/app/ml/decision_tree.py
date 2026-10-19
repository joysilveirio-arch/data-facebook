from sklearn.tree import DecisionTreeClassifier

def build_classifier(
    max_depth: int | None = None,
    min_samples_split: int = 2,
    random_state: int = 42,
) -> DecisionTreeClassifier:
    return DecisionTreeClassifier(
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        random_state=random_state,
        class_weight="balanced",
    )