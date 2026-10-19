from typing import List, Dict, Any

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    confusion_matrix,
)


def evaluate(
    y_true: List[str],
    y_pred: List[str],
    classes: List[str],
) -> Dict[str, Any]:
    """
    Evaluate sentiment classification model.

    Metrics:
    - Accuracy
    - Macro F1-score
    - Macro Precision
    - Macro Recall
    - Confusion Matrix

    All score values are returned between 0.0 and 1.0.
    """

    if len(y_true) != len(y_pred):
        raise ValueError(
            "Jumlah label aktual berbeda dengan jumlah prediksi."
        )

    if not y_true:
        raise ValueError(
            "Data evaluasi kosong. Tambahkan data terlebih dahulu."
        )

    if not classes:
        raise ValueError(
            "Daftar kelas sentimen tidak boleh kosong."
        )

    # Normalisasi label supaya konsisten.
    y_true = [str(label).strip().lower() for label in y_true]
    y_pred = [str(label).strip().lower() for label in y_pred]
    classes = [str(label).strip().lower() for label in classes]

    # Hitung confusion matrix dengan urutan kelas yang tetap.
    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=classes,
    )

    # Hitung metrik evaluasi.
    accuracy = float(accuracy_score(y_true, y_pred))

    f1_macro = float(
        f1_score(
            y_true,
            y_pred,
            labels=classes,
            average="macro",
            zero_division=0,
        )
    )

    precision_macro = float(
        precision_score(
            y_true,
            y_pred,
            labels=classes,
            average="macro",
            zero_division=0,
        )
    )

    recall_macro = float(
        recall_score(
            y_true,
            y_pred,
            labels=classes,
            average="macro",
            zero_division=0,
        )
    )

    return {
        "accuracy": accuracy,
        "f1_macro": f1_macro,
        "precision_macro": precision_macro,
        "recall_macro": recall_macro,
        "confusion_matrix": matrix.tolist(),
    }
