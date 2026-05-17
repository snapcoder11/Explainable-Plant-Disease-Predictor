import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from pathlib import Path
from sklearn.metrics import confusion_matrix, roc_curve, auc
from sklearn.preprocessing import label_binarize
import torch
from model import PlantDiseaseCBM, NUM_CONCEPTS, CONCEPT_NAMES
from dataset import get_dataloaders, PlantDiseaseDataset, get_val_transforms

PLANTVILLAGE_DIR = "data/plantvillage/plantvillage dataset/color"
PLANTDOC_DIR     = "data/plantdoc/PlantDoc-Dataset"
CHECKPOINT       = "outputs/checkpoints/best_model.pth"
OUTPUT_DIR       = "outputs/figures"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ── Load model ────────────────────────────────────────────
print("Loading model...")
ckpt = torch.load(CHECKPOINT, map_location=device)
num_classes = ckpt["num_classes"]
model = PlantDiseaseCBM(num_classes=num_classes, num_concepts=NUM_CONCEPTS, pretrained=False).to(device)
model.load_state_dict(ckpt["model"])
model.eval()

# ── Load data ─────────────────────────────────────────────
print("Loading data...")
loaders, _ = get_dataloaders(PLANTVILLAGE_DIR, PLANTDOC_DIR, batch_size=32)

pv_dataset = PlantDiseaseDataset(PLANTVILLAGE_DIR, get_val_transforms(), split="val")
class_names = [None] * len(pv_dataset.class_to_idx)
for name, idx in pv_dataset.class_to_idx.items():
    class_names[idx] = name

# Short names for plotting
short_names = [n.replace("___", "\n").replace("_", " ")[:25] for n in class_names]

# ── Collect predictions ───────────────────────────────────
def get_preds_and_concepts(loader):
    all_preds, all_targets, all_concepts = [], [], []
    with torch.no_grad():
        for batch in loader:
            images      = batch["image"].to(device)
            targets     = batch["label"]
            concepts_gt = batch["concepts"].to(device)
            logits, concepts, _ = model(images)
            preds = logits.argmax(dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_targets.extend(targets.numpy())
            all_concepts.append(concepts.cpu().numpy())
    return np.array(all_preds), np.array(all_targets), np.concatenate(all_concepts)

print("Getting predictions...")
val_preds,  val_targets,  val_concepts  = get_preds_and_concepts(loaders["val"])
test_preds, test_targets, test_concepts = get_preds_and_concepts(loaders["test"])
field_preds, field_targets, field_concepts = get_preds_and_concepts(loaders["test_field"])

# =============================================================
# FIGURE 1 — Confusion Matrix (Validation)
# =============================================================
print("Plotting confusion matrix...")
cm = confusion_matrix(val_targets, val_preds)
fig, ax = plt.subplots(figsize=(22, 18))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=short_names, yticklabels=short_names,
            ax=ax, linewidths=0.5, annot_kws={"size": 6})
ax.set_xlabel("Predicted Label", fontsize=13)
ax.set_ylabel("True Label", fontsize=13)
ax.set_title("Confusion Matrix — Validation Set (PlantVillage)", fontsize=15, fontweight="bold")
plt.xticks(rotation=45, ha="right", fontsize=7)
plt.yticks(rotation=0, fontsize=7)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig1_confusion_matrix_val.png", dpi=150, bbox_inches="tight")
plt.close()
print("✅ Figure 1 saved")

# =============================================================
# FIGURE 2 — Per Class Metrics Bar Chart
# =============================================================
print("Plotting per-class metrics...")
from sklearn.metrics import precision_recall_fscore_support
precision, recall, f1, support = precision_recall_fscore_support(
    val_targets, val_preds, zero_division=0
)

x = np.arange(len(class_names))
width = 0.25

fig, ax = plt.subplots(figsize=(24, 8))
bars1 = ax.bar(x - width, precision, width, label="Precision", color="#3498DB", alpha=0.85)
bars2 = ax.bar(x,         recall,    width, label="Recall",    color="#2ECC71", alpha=0.85)
bars3 = ax.bar(x + width, f1,        width, label="F1 Score",  color="#E74C3C", alpha=0.85)

ax.set_xlabel("Disease Class", fontsize=12)
ax.set_ylabel("Score", fontsize=12)
ax.set_title("Per-Class Precision, Recall, F1 Score — Validation Set", fontsize=14, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(short_names, rotation=45, ha="right", fontsize=7)
ax.set_ylim(0, 1.1)
ax.legend(fontsize=11)
ax.axhline(y=0.95, color="gray", linestyle="--", alpha=0.5, label="0.95 threshold")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig2_per_class_metrics.png", dpi=150, bbox_inches="tight")
plt.close()
print("✅ Figure 2 saved")

# =============================================================
# FIGURE 3 — Training History (Accuracy + Loss)
# =============================================================
print("Plotting training history...")
results_path = Path("outputs/checkpoints/results.json")
if results_path.exists():
    with open(results_path) as f:
        results = json.load(f)
    history = results["history"]
    epochs     = [h["epoch"]     for h in history]
    train_accs = [h["train_acc"] for h in history]
    val_accs   = [h["val_acc"]   for h in history]
    train_f1s  = [h["train_f1"]  for h in history]
    val_f1s    = [h["val_f1"]    for h in history]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(epochs, train_accs, "b-o", markersize=3, label="Train Accuracy", linewidth=2)
    ax1.plot(epochs, val_accs,   "r-o", markersize=3, label="Val Accuracy",   linewidth=2)
    ax1.set_xlabel("Epoch", fontsize=12)
    ax1.set_ylabel("Accuracy", fontsize=12)
    ax1.set_title("Training vs Validation Accuracy", fontsize=13, fontweight="bold")
    ax1.legend(fontsize=11)
    ax1.grid(alpha=0.3)
    ax1.set_ylim(0, 1.05)

    ax2.plot(epochs, train_f1s, "b-o", markersize=3, label="Train F1", linewidth=2)
    ax2.plot(epochs, val_f1s,   "r-o", markersize=3, label="Val F1",   linewidth=2)
    ax2.set_xlabel("Epoch", fontsize=12)
    ax2.set_ylabel("F1 Score", fontsize=12)
    ax2.set_title("Training vs Validation F1 Score", fontsize=13, fontweight="bold")
    ax2.legend(fontsize=11)
    ax2.grid(alpha=0.3)
    ax2.set_ylim(0, 1.05)

    plt.suptitle("Training History — Plant Disease CBM", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/fig3_training_history.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("✅ Figure 3 saved")
else:
    print("⚠️ results.json not found — skipping training history plot")

# =============================================================
# FIGURE 4 — Dataset Comparison Bar Chart
# =============================================================
print("Plotting dataset comparison...")
datasets    = ["Validation\n(PlantVillage)", "Test\n(Combined)", "Field Test\n(PlantDoc)"]
accuracies  = [0.9991, 0.9925, 0.6687]
precisions  = [0.9968, 0.9827, 0.6498]
recalls     = [0.9989, 0.9828, 0.6478]
f1_scores   = [0.9978, 0.9827, 0.6262]

x     = np.arange(len(datasets))
width = 0.2

fig, ax = plt.subplots(figsize=(12, 6))
ax.bar(x - 1.5*width, accuracies,  width, label="Accuracy",  color="#3498DB", alpha=0.85)
ax.bar(x - 0.5*width, precisions,  width, label="Precision", color="#2ECC71", alpha=0.85)
ax.bar(x + 0.5*width, recalls,     width, label="Recall",    color="#E74C3C", alpha=0.85)
ax.bar(x + 1.5*width, f1_scores,   width, label="F1 Score",  color="#9B59B6", alpha=0.85)

ax.set_xlabel("Dataset", fontsize=12)
ax.set_ylabel("Score", fontsize=12)
ax.set_title("Performance Across Datasets", fontsize=14, fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(datasets, fontsize=11)
ax.set_ylim(0, 1.1)
ax.legend(fontsize=11)
ax.axhline(y=0.95, color="gray", linestyle="--", alpha=0.5)

for i, (acc, prec, rec, f1) in enumerate(zip(accuracies, precisions, recalls, f1_scores)):
    ax.text(i - 1.5*width, acc  + 0.01, f"{acc:.2f}",  ha="center", fontsize=8, fontweight="bold")
    ax.text(i - 0.5*width, prec + 0.01, f"{prec:.2f}", ha="center", fontsize=8, fontweight="bold")
    ax.text(i + 0.5*width, rec  + 0.01, f"{rec:.2f}",  ha="center", fontsize=8, fontweight="bold")
    ax.text(i + 1.5*width, f1   + 0.01, f"{f1:.2f}",   ha="center", fontsize=8, fontweight="bold")

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig4_dataset_comparison.png", dpi=150, bbox_inches="tight")
plt.close()
print("✅ Figure 4 saved")

# =============================================================
# FIGURE 5 — Concept Activation Heatmap
# =============================================================
print("Plotting concept activation heatmap...")
concept_means = []
for cls_idx in range(num_classes):
    mask = val_targets == cls_idx
    if mask.sum() > 0:
        concept_means.append(val_concepts[mask].mean(axis=0))
    else:
        concept_means.append(np.zeros(NUM_CONCEPTS))

concept_matrix = np.array(concept_means)

fig, ax = plt.subplots(figsize=(16, 14))
sns.heatmap(concept_matrix, annot=True, fmt=".2f", cmap="YlOrRd",
            xticklabels=CONCEPT_NAMES,
            yticklabels=short_names,
            ax=ax, linewidths=0.5,
            annot_kws={"size": 7})
ax.set_xlabel("Agronomic Concepts", fontsize=12)
ax.set_ylabel("Disease Class", fontsize=12)
ax.set_title("Concept Activation Heatmap\n(Mean concept score per disease class)", 
             fontsize=14, fontweight="bold")
plt.xticks(rotation=45, ha="right", fontsize=9)
plt.yticks(rotation=0, fontsize=7)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig5_concept_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()
print("✅ Figure 5 saved")

# =============================================================
# FIGURE 6 — Summary Metrics Card
# =============================================================
print("Plotting summary metrics...")
fig, axes = plt.subplots(1, 4, figsize=(16, 5))
fig.suptitle("Model Performance Summary — Plant Disease CBM", 
             fontsize=15, fontweight="bold", y=1.02)

metrics = [
    ("Validation\nAccuracy", 99.91, "#3498DB"),
    ("Test\nAccuracy",       99.25, "#2ECC71"),
    ("Test\nF1 Score",       98.27, "#E74C3C"),
    ("Field Test\nAccuracy", 66.87, "#9B59B6"),
]

for ax, (title, value, color) in zip(axes, metrics):
    ax.pie([value, 100-value], colors=[color, "#ECF0F1"],
           startangle=90, counterclock=False,
           wedgeprops={"linewidth": 2, "edgecolor": "white"})
    ax.text(0, 0, f"{value:.1f}%", ha="center", va="center",
            fontsize=18, fontweight="bold", color=color)
    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig6_summary_metrics.png", dpi=150, bbox_inches="tight")
plt.close()
print("✅ Figure 6 saved")

# =============================================================
# DONE
# =============================================================
print(f"\n{'='*50}")
print("ALL FIGURES SAVED to outputs/figures/")
print("="*50)
print("fig1 — Confusion Matrix (Validation)")
print("fig2 — Per-Class Precision/Recall/F1")
print("fig3 — Training History")
print("fig4 — Dataset Comparison")
print("fig5 — Concept Activation Heatmap")
print("fig6 — Summary Metrics")
print("\n✅ Ready for paper!")