import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score,
    recall_score, classification_report, confusion_matrix
)
from pathlib import Path
from model import PlantDiseaseCBM, CBMLoss, NUM_CONCEPTS
from dataset import get_dataloaders

PLANTVILLAGE_DIR = "data/plantvillage/plantvillage dataset/color"
PLANTDOC_DIR     = "data/plantdoc/PlantDoc-Dataset"
CHECKPOINT       = "outputs/checkpoints/best_model.pth"
OUTPUT_DIR       = "outputs/figures"

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Loading checkpoint...")
ckpt = torch.load(CHECKPOINT, map_location=device)
print(f"Checkpoint from epoch : {ckpt['epoch'] + 1}")
print(f"Best val acc recorded : {ckpt['best_val_acc']:.4f}")
num_classes = ckpt["num_classes"]

print("\nLoading datasets...")
loaders, _ = get_dataloaders(
    plantvillage_dir=PLANTVILLAGE_DIR,
    plantdoc_dir=PLANTDOC_DIR,
    batch_size=32,
)

print("\nBuilding model...")
model = PlantDiseaseCBM(
    num_classes=num_classes,
    num_concepts=NUM_CONCEPTS,
    pretrained=False
).to(device)
model.load_state_dict(ckpt["model"])
model.eval()

def evaluate(loader, name, class_names=None, save_cm=True):
    all_preds, all_targets = [], []

    with torch.no_grad():
        for batch in loader:
            images      = batch["image"].to(device)
            targets     = batch["label"].to(device)
            concepts_gt = batch["concepts"].to(device)
            logits, concepts, _ = model(images)
            preds = logits.argmax(dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_targets.extend(targets.cpu().numpy())

    # ── Metrics ───────────────────────────────────────────
    acc       = accuracy_score(all_targets, all_preds)
    f1        = f1_score(all_targets, all_preds, average="macro", zero_division=0)
    precision = precision_score(all_targets, all_preds, average="macro", zero_division=0)
    recall    = recall_score(all_targets, all_preds, average="macro", zero_division=0)

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    print(f"  Accuracy  : {acc:.4f} ({acc*100:.2f}%)")
    print(f"  Precision : {precision:.4f} ({precision*100:.2f}%)")
    print(f"  Recall    : {recall:.4f} ({recall*100:.2f}%)")
    print(f"  F1 Score  : {f1:.4f} ({f1*100:.2f}%)")

    # ── Per class report ──────────────────────────────────
    if class_names:
        labels = list(range(len(class_names)))
        report = classification_report(
            all_targets, all_preds,
            labels=labels,
            target_names=class_names,
            zero_division=0
        )
        print(f"\nPer-Class Report:\n{report}")

        # Save report to file
        report_path = f"{OUTPUT_DIR}/{name.replace(' ', '_').replace('(', '').replace(')', '')}_report.txt"
        with open(report_path, "w") as f:
            f.write(f"{name}\n")
            f.write(f"Accuracy  : {acc:.4f}\n")
            f.write(f"Precision : {precision:.4f}\n")
            f.write(f"Recall    : {recall:.4f}\n")
            f.write(f"F1 Score  : {f1:.4f}\n\n")
            f.write(report)
        print(f"Report saved: {report_path}")

    # ── Confusion Matrix ──────────────────────────────────
    if save_cm and class_names:
        cm = confusion_matrix(all_targets, all_preds)
        fig, ax = plt.subplots(figsize=(20, 16))
        sns.heatmap(
            cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=class_names,
            yticklabels=class_names,
            ax=ax
        )
        ax.set_xlabel("Predicted", fontsize=12)
        ax.set_ylabel("Actual", fontsize=12)
        ax.set_title(f"Confusion Matrix — {name}", fontsize=14)
        plt.xticks(rotation=45, ha="right", fontsize=7)
        plt.yticks(rotation=0, fontsize=7)
        plt.tight_layout()
        cm_path = f"{OUTPUT_DIR}/{name.replace(' ', '_').replace('(', '').replace(')', '')}_confusion_matrix.png"
        plt.savefig(cm_path, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"Confusion matrix saved: {cm_path}")

    return acc, precision, recall, f1, all_preds, all_targets

# ── Get class names ───────────────────────────────────────
from dataset import PlantDiseaseDataset, get_val_transforms
pv_dataset = PlantDiseaseDataset(
    PLANTVILLAGE_DIR,
    get_val_transforms(),
    split="val"
)
class_names = [None] * len(pv_dataset.class_to_idx)
for name, idx in pv_dataset.class_to_idx.items():
    class_names[idx] = name

# ── Run evaluations ───────────────────────────────────────
val_acc, val_prec, val_rec, val_f1, _, _ = evaluate(
    loaders["val"], "Validation PlantVillage", class_names
)
test_acc, test_prec, test_rec, test_f1, _, _ = evaluate(
    loaders["test"], "Test Combined", class_names
)
field_acc, field_prec, field_rec, field_f1, _, _ = evaluate(
    loaders["test_field"], "Field Test PlantDoc", save_cm=False
)

# ── Summary table ─────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  FINAL SUMMARY")
print(f"{'='*60}")
print(f"  {'Dataset':<25} {'Acc':>8} {'Prec':>8} {'Rec':>8} {'F1':>8}")
print(f"  {'-'*57}")
print(f"  {'Validation (PlantVillage)':<25} {val_acc:>8.4f} {val_prec:>8.4f} {val_rec:>8.4f} {val_f1:>8.4f}")
print(f"  {'Test (Combined)':<25} {test_acc:>8.4f} {test_prec:>8.4f} {test_rec:>8.4f} {test_f1:>8.4f}")
print(f"  {'Field Test (PlantDoc)':<25} {field_acc:>8.4f} {field_prec:>8.4f} {field_rec:>8.4f} {field_f1:>8.4f}")
print(f"{'='*60}")
print(f"\n✅ All metrics saved to outputs/figures/")