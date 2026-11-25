"""Linear SVM model (M2) — character TF-IDF representation."""
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV


def build_linear_svm(C=1.0, class_weight="balanced", max_iter=2000, random_state=42,
                     calibrate=True, cv=3):
    base = LinearSVC(C=C, class_weight=class_weight, max_iter=max_iter,
                     random_state=random_state, dual="auto")
    if calibrate:
        return CalibratedClassifierCV(base, method="sigmoid", cv=cv)
    return base
