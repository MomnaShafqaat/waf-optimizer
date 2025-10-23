import pandas as pd
import numpy as np

def tune_threshold(log_file_path="data/traffic.csv", step=0.05):
    """
    Adjust firewall sensitivity threshold.
    log_file_path -> CSV must have 'score' and 'actual_label' columns
    step -> threshold testing increment (0.05 = test 0.0, 0.05, 0.1, ...)
    """

    df = pd.read_csv(log_file_path)

    # ensure required columns
    if "score" not in df.columns or "actual_label" not in df.columns:
        raise ValueError("traffic.csv must contain 'score' and 'actual_label' columns")

    best_threshold = 0.5
    best_accuracy = 0
    results = []

    for th in np.arange(0, 1.0, step):
        df["predicted"] = (df["score"] >= th).astype(int)

        TP = ((df["actual_label"] == 1) & (df["predicted"] == 1)).sum()
        TN = ((df["actual_label"] == 0) & (df["predicted"] == 0)).sum()
        FP = ((df["actual_label"] == 0) & (df["predicted"] == 1)).sum()
        FN = ((df["actual_label"] == 1) & (df["predicted"] == 0)).sum()

        accuracy = (TP + TN) / (TP + TN + FP + FN + 1e-6)
        fpr = FP / (FP + TN + 1e-6)
        fnr = FN / (FN + TP + 1e-6)

        results.append({
            "threshold": round(th, 2),
            "accuracy": round(accuracy, 3),
            "false_positive_rate": round(fpr, 3),
            "false_negative_rate": round(fnr, 3)
        })

        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_threshold = th

    results_df = pd.DataFrame(results)
    return best_threshold, results_df
