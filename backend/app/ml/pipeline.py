
import json
import math
from typing import Any

import numpy as np
from sklearn.model_selection import train_test_split

from backend.app.core.config import settings
from backend.app.ml.preprocessor import clean_text
from backend.app.ml.vectorizer import build_vectorizer
from backend.app.ml.decision_tree import build_classifier
from backend.app.ml.evaluator import evaluate
from backend.app.ml import persistence


class MLPipeline:
    """
    Pipeline klasifikasaun sentimentu:
    1. Valida dadus no label.
    2. Preprocessa testu no ignora testu ne'ebé sai mamuk.
    3. Verifika distribuisaun klase depois preprocessing.
    4. Fahe dadus ba training no testing.
    5. Treina TF-IDF ho training data de'it.
    6. Treina Decision Tree.
    7. Avalia modelu ho test set.
    8. Valida metrics no confusion matrix.
    9. Rai modelu no metadata.
    """

    def __init__(self) -> None:
        self.model = None
        self.vectorizer = None
        self.classes: list[str] = []
        self.meta: dict[str, Any] = {}

    # --------------------------------------------------
    # TRAIN
    # --------------------------------------------------
    def train(
        self,
        texts: list[str],
        labels: list[str],
        *,
        test_size: float | None = None,
        max_depth: int | None = None,
        min_samples_split: int = 2,
        random_state: int | None = None,
    ) -> dict[str, Any]:

        # 1. Validasaun input
        if not isinstance(texts, (list, tuple)):
            raise ValueError(
                "Daftar teks harus berupa list atau tuple."
            )

        if not isinstance(labels, (list, tuple)):
            raise ValueError(
                "Daftar label harus berupa list atau tuple."
            )

        if len(texts) != len(labels):
            raise ValueError(
                "Jumlah teks dan label tidak sama."
            )

        if not texts:
            raise ValueError(
                "Tidak ada data berlabel untuk training."
            )

        if len(texts) < settings.MIN_SAMPLES_TO_TRAIN:
            raise ValueError(
                f"Minimal {settings.MIN_SAMPLES_TO_TRAIN} "
                "sampel berlabel diperlukan untuk training. "
                f"Saat ini tersedia {len(texts)} sampel."
            )

        # 2. Normaliza testu no label hamutuk.
        # Testu original mamuk la bele uza ba training.
        normalized_texts: list[str] = []
        normalized_labels: list[str] = []

        for index, (text, label) in enumerate(
            zip(texts, labels),
            start=1,
        ):
            if not isinstance(text, str) or not text.strip():
                raise ValueError(
                    f"Teks kosong atau tidak valid pada sampel "
                    f"ke-{index}. Periksa data berlabel."
                )

            if label is None:
                raise ValueError(
                    f"Label kosong pada sampel ke-{index}."
                )

            normalized_label = str(label).strip().lower()

            if not normalized_label:
                raise ValueError(
                    f"Label kosong pada sampel ke-{index}."
                )

            normalized_texts.append(text.strip())
            normalized_labels.append(normalized_label)

        # 3. Validasaun parameter
        if test_size is None:
            test_size = settings.TEST_SIZE

        try:
            test_size = float(test_size)
        except (TypeError, ValueError):
            raise ValueError(
                "Test Size harus berupa angka, contohnya 0.2."
            ) from None

        if not math.isfinite(test_size) or not 0 < test_size < 1:
            raise ValueError(
                "Test Size harus lebih besar dari 0 dan "
                "lebih kecil dari 1. Contoh: 0.2."
            )

        if isinstance(min_samples_split, bool):
            raise ValueError(
                "Min Samples Split harus berupa bilangan bulat."
            )

        try:
            min_samples_split = int(min_samples_split)
        except (TypeError, ValueError):
            raise ValueError(
                "Min Samples Split harus berupa bilangan bulat."
            ) from None

        if min_samples_split < 2:
            raise ValueError(
                "Min Samples Split minimal 2."
            )

        if max_depth is not None:
            if isinstance(max_depth, bool):
                raise ValueError(
                    "Max Depth harus berupa bilangan bulat "
                    "positif atau dikosongkan."
                )

            try:
                max_depth = int(max_depth)
            except (TypeError, ValueError):
                raise ValueError(
                    "Max Depth harus berupa bilangan bulat "
                    "positif atau dikosongkan."
                ) from None

            if max_depth < 1:
                raise ValueError(
                    "Max Depth harus minimal 1 atau dikosongkan."
                )

        if random_state is None:
            random_state = settings.RANDOM_STATE

        if isinstance(random_state, bool):
            raise ValueError(
                "Random State harus berupa bilangan bulat."
            )

        try:
            random_state = int(random_state)
        except (TypeError, ValueError):
            raise ValueError(
                "Random State harus berupa bilangan bulat."
            ) from None

        # 4. Preprocessing.
        # Importante: testu no label filtra hamutuk.
        # Se testu sai mamuk, ignora nia amostra,
        # maibe la ignora label mesak.
        processed_texts: list[str] = []
        processed_labels: list[str] = []
        skipped_empty = 0

        for index, (text, label) in enumerate(
            zip(normalized_texts, normalized_labels),
            start=1,
        ):
            try:
                cleaned = clean_text(text)
            except Exception as exc:
                raise ValueError(
                    f"Preprocessing gagal pada sampel "
                    f"ke-{index}: {exc}"
                ) from exc

            cleaned = (
                cleaned.strip()
                if isinstance(cleaned, str)
                else ""
            )

            if not cleaned:
                skipped_empty += 1
                continue

            processed_texts.append(cleaned)
            processed_labels.append(label)

        clean_texts = processed_texts
        normalized_labels = processed_labels

        # 5. Verifika quantidade depois preprocessing.
        n_total = len(clean_texts)

        if n_total == 0:
            raise ValueError(
                "Semua teks menjadi kosong setelah preprocessing. "
                "Periksa preprocessor.py dan data sumber."
            )

        if n_total < settings.MIN_SAMPLES_TO_TRAIN:
            raise ValueError(
                f"Setelah preprocessing hanya tersisa {n_total} "
                f"sampel valid; minimal "
                f"{settings.MIN_SAMPLES_TO_TRAIN} sampel diperlukan. "
                f"{skipped_empty} sampel kosong dilewati. "
                "Tambahkan data berlabel dengan teks yang valid."
            )

        print(
            f"[ML] Preprocessing selesai: {n_total} sampel valid; "
            f"{skipped_empty} sampel kosong dilewati."
        )

        # 6. Verifika klase sentimentu depois filtering.
        classes = sorted(set(normalized_labels))

        if len(classes) < 2:
            raise ValueError(
                "Training membutuhkan minimal dua kelas "
                "sentimen berbeda setelah preprocessing. "
                "Periksa label pada halaman Labeling."
            )

        class_counts = {
            label: normalized_labels.count(label)
            for label in classes
        }

        insufficient = {
            label: count
            for label, count in class_counts.items()
            if count < 2
        }

        if insufficient:
            details = ", ".join(
                f"{label}: {count} sampel"
                for label, count in insufficient.items()
            )
            raise ValueError(
                "Jumlah sampel per kelas belum cukup setelah "
                f"preprocessing. Kelas yang kurang: {details}. "
                "Tambahkan label sentimen yang benar melalui "
                "halaman Labeling, lalu jalankan training kembali."
            )

        # 7. Verifika tamanho train/test antes split.
        n_test_expected = math.ceil(n_total * test_size)
        n_train_expected = n_total - n_test_expected
        n_classes = len(classes)

        if n_test_expected < n_classes:
            raise ValueError(
                f"Test Size {test_size} menghasilkan "
                f"{n_test_expected} sampel testing, sedangkan "
                f"ada {n_classes} kelas. Tingkatkan Test Size "
                "atau tambahkan data berlabel."
            )

        if n_train_expected < n_classes:
            raise ValueError(
                "Jumlah sampel training tidak cukup untuk "
                "mencakup semua kelas. Tambahkan data berlabel "
                "atau sesuaikan Test Size."
            )

        # 8. Split estratifikadu.
        try:
            (
                X_train_text,
                X_test_text,
                y_train,
                y_test,
            ) = train_test_split(
                clean_texts,
                normalized_labels,
                test_size=test_size,
                random_state=random_state,
                stratify=normalized_labels,
            )
        except ValueError as exc:
            raise ValueError(
                "Pembagian data training/testing gagal. "
                "Periksa jumlah sampel per kelas dan Test Size. "
                f"Detail: {exc}"
            ) from exc

        train_classes = set(y_train)
        missing_train_classes = set(classes) - train_classes

        if missing_train_classes:
            raise ValueError(
                "Training set tidak mencakup semua kelas: "
                + ", ".join(sorted(missing_train_classes))
            )

        # 9. TF-IDF: fit ba training data de'it.
        vec = build_vectorizer()

        try:
            X_train = vec.fit_transform(X_train_text)
            X_test = vec.transform(X_test_text)
        except ValueError as exc:
            raise ValueError(
                "TF-IDF gagal memproses data teks. Periksa "
                "isi teks dan konfigurasi vectorizer.py. "
                f"Detail: {exc}"
            ) from exc

        if X_train.shape[1] == 0:
            raise ValueError(
                "TF-IDF tidak menemukan fitur teks yang valid."
            )

        # 10. Treina Decision Tree.
        clf = build_classifier(
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            random_state=random_state,
        )

        try:
            clf.fit(X_train, y_train)
            y_pred = clf.predict(X_test)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                "Training atau prediksi Decision Tree gagal. "
                f"Detail: {exc}"
            ) from exc

        model_classes = [str(c) for c in clf.classes_]

        # 11. Avaliasaun.
        metrics = evaluate(
            list(y_test),
            list(y_pred),
            classes,
        )

        required_metrics = (
            "accuracy",
            "f1_macro",
            "precision_macro",
            "recall_macro",
            "confusion_matrix",
        )

        missing_metrics = [
            name for name in required_metrics
            if name not in metrics
        ]

        if missing_metrics:
            raise ValueError(
                "Evaluator tidak menghasilkan metrik: "
                + ", ".join(missing_metrics)
            )

        # 12. Valida confusion matrix.
        matrix = np.asarray(
            metrics["confusion_matrix"],
            dtype=int,
        )

        expected_shape = (len(classes), len(classes))

        if matrix.shape != expected_shape:
            raise ValueError(
                "Ukuran confusion matrix tidak sesuai. "
                f"Seharusnya {expected_shape}, "
                f"tetapi hasilnya {matrix.shape}."
            )

        if np.any(matrix < 0):
            raise ValueError(
                "Confusion matrix tidak boleh berisi "
                "jumlah sampel negatif."
            )

        total_test = int(matrix.sum())

        if total_test != len(y_test):
            raise ValueError(
                "Jumlah pada confusion matrix tidak sama "
                "dengan jumlah sampel testing."
            )

        if total_test == 0:
            raise ValueError(
                "Tidak ada sampel testing untuk evaluasi."
            )

        # 13. Valida Accuracy ho confusion matrix.
        correct = int(np.trace(matrix))
        calculated_accuracy = correct / total_test

        try:
            reported_accuracy = float(metrics["accuracy"])
        except (TypeError, ValueError):
            raise ValueError(
                "Accuracy dari evaluator bukan angka valid."
            ) from None

        if not math.isfinite(reported_accuracy):
            raise ValueError(
                "Accuracy dari evaluator bukan angka valid."
            )

        # Aceita accuracy iha escala 0-1 ka 0-100.
        if 1.0 < reported_accuracy <= 100.0:
            reported_accuracy /= 100.0

        if not 0.0 <= reported_accuracy <= 1.0:
            raise ValueError(
                "Accuracy harus berada antara 0 dan 1 "
                "(atau 0 sampai 100 jika berbentuk persen)."
            )

        if not np.isclose(
            calculated_accuracy,
            reported_accuracy,
            atol=1e-6,
        ):
            raise ValueError(
                "Accuracy tidak sesuai dengan confusion matrix. "
                f"Accuracy matrix={calculated_accuracy:.6f}, "
                f"accuracy evaluator={reported_accuracy:.6f}. "
                "Periksa evaluator.py."
            )

        metrics["accuracy"] = calculated_accuracy

        for metric_name in (
            "f1_macro",
            "precision_macro",
            "recall_macro",
        ):
            try:
                value = float(metrics[metric_name])
            except (TypeError, ValueError):
                raise ValueError(
                    f"Metrik {metric_name} bukan angka valid."
                ) from None

            if not math.isfinite(value):
                raise ValueError(
                    f"Metrik {metric_name} bukan angka valid."
                )

            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"Metrik {metric_name} harus berada "
                    "antara 0 dan 1."
                )

            metrics[metric_name] = value

        # 14. Metadata.
        meta = {
            "n_samples": int(n_total),
            "n_train": int(len(y_train)),
            "n_test": int(len(y_test)),
            "n_classes": int(len(classes)),
            "classes": classes,
            "model_classes": model_classes,
            "feature_count": int(X_train.shape[1]),
            "class_counts": class_counts,
            "skipped_empty": int(skipped_empty),
            "test_size": float(test_size),
            **metrics,
        }

        # 15. Rai modelu no metadata.
        persistence.save_pipeline(
            {
                "model": clf,
                "vectorizer": vec,
                "classes": model_classes,
                "meta": meta,
            },
            meta,
        )

        # Atualiza estado depois persisténsia susesu.
        self.model = clf
        self.vectorizer = vec
        self.classes = model_classes
        self.meta = meta

        return self.meta

    # --------------------------------------------------
    # LOAD
    # --------------------------------------------------
    def load(self) -> bool:
        payload = persistence.load_pipeline()

        if not payload:
            return False

        model = payload.get("model")
        vectorizer = payload.get("vectorizer")

        if model is None or vectorizer is None:
            return False

        self.model = model
        self.vectorizer = vectorizer

        if hasattr(self.model, "classes_"):
            self.classes = [
                str(c) for c in self.model.classes_
            ]
        else:
            self.classes = payload.get("classes", [])

        self.meta = (
            payload.get("meta")
            or persistence.load_meta()
            or {}
        )

        return True

    def is_ready(self) -> bool:
        if self.model is None or self.vectorizer is None:
            return self.load()

        return True

    # --------------------------------------------------
    # PREDICT ONE
    # --------------------------------------------------
    def predict_one(self, text: str) -> dict[str, Any]:
        if not self.is_ready():
            raise RuntimeError(
                "Model belum dilatih. Latih model terlebih dahulu."
            )

        if not isinstance(text, str) or not text.strip():
            raise ValueError(
                "Teks untuk prediksi tidak boleh kosong."
            )

        cleaned = clean_text(text) or text.strip()

        X = self.vectorizer.transform([cleaned])
        probabilities = self.model.predict_proba(X)[0]

        model_classes = [
            str(c) for c in self.model.classes_
        ]

        idx = int(np.argmax(probabilities))

        return {
            "text": text,
            "clean": cleaned,
            "label": model_classes[idx],
            "confidence": float(probabilities[idx]),
            "probabilities": {
                str(label): float(probability)
                for label, probability in zip(
                    model_classes,
                    probabilities,
                )
            },
        }

    # --------------------------------------------------
    # PREDICT MANY
    # --------------------------------------------------
    def predict_many(
        self,
        texts: list[str],
    ) -> list[dict[str, Any]]:
        if not isinstance(texts, (list, tuple)):
            raise ValueError(
                "Daftar teks untuk prediksi harus berupa list."
            )

        return [
            self.predict_one(text)
            for text in texts
        ]

    # --------------------------------------------------
    # METADATA JSON
    # --------------------------------------------------
    def meta_json(self) -> str:
        return json.dumps(
            self.meta,
            ensure_ascii=False,
            allow_nan=False,
        )


# Singleton
ml_pipeline = MLPipeline()
