import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from model import PlantDiseaseCBM, NUM_CONCEPTS, CONCEPT_NAMES
from dataset import get_dataloaders, PlantDiseaseDataset, get_val_transforms

PLANTVILLAGE_DIR = "data/plantvillage/plantvillage dataset/color"
PLANTDOC_DIR     = "data/plantdoc/PlantDoc-Dataset"
CHECKPOINT       = "outputs/checkpoints/best_model.pth"
OUTPUT_DIR       = "outputs/xai"
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}")

# ── Load model ────────────────────────────────────────────
print("Loading model...")
ckpt        = torch.load(CHECKPOINT, map_location=device)
num_classes = ckpt["num_classes"]
model       = PlantDiseaseCBM(num_classes=num_classes, num_concepts=NUM_CONCEPTS, pretrained=False).to(device)
model.load_state_dict(ckpt["model"])
model.eval()

# ── Load data ─────────────────────────────────────────────
print("Loading data...")
loaders, _ = get_dataloaders(PLANTVILLAGE_DIR, PLANTDOC_DIR, batch_size=32)

pv_dataset  = PlantDiseaseDataset(PLANTVILLAGE_DIR, get_val_transforms(), split="val")
class_names = [None] * len(pv_dataset.class_to_idx)
for name, idx in pv_dataset.class_to_idx.items():
    class_names[idx] = name

short_names = [n.replace("___", " ").replace("_", " ")[:20] for n in class_names]

# ── Collect concepts and targets ──────────────────────────
print("Collecting concepts...")
all_concepts, all_targets, all_preds = [], [], []
with torch.no_grad():
    for batch in loaders["val"]:
        images   = batch["image"].to(device)
        targets  = batch["label"]
        logits, concepts, _ = model(images)
        preds = logits.argmax(dim=1).cpu()
        all_concepts.append(concepts.cpu())
        all_targets.append(targets)
        all_preds.append(preds)

all_concepts = torch.cat(all_concepts)
all_targets  = torch.cat(all_targets)
all_preds    = torch.cat(all_preds)
print(f"Collected {len(all_concepts)} samples")

# =============================================================
# 1. COUNTERFACTUAL EXPLANATION
# =============================================================
print("\n[1/4] Generating counterfactuals...")

def generate_counterfactual(model, concepts, original_class, target_class,
                             max_iter=300, lr=0.05, lambda_sparse=0.1, lambda_close=0.5):
    concepts   = concepts.unsqueeze(0).to(device)
    delta      = torch.zeros_like(concepts, requires_grad=True)
    optimizer  = torch.optim.Adam([delta], lr=lr)
    best_delta = None
    best_loss  = float("inf")

    for _ in range(max_iter):
        optimizer.zero_grad()
        perturbed = torch.clamp(concepts + delta, 0.0, 1.0)
        logits    = model.predict_from_concepts(perturbed)
        task_loss = nn.CrossEntropyLoss()(logits, torch.tensor([target_class], device=device))
        sparse    = delta.abs().sum()
        close     = (delta ** 2).sum()
        loss      = task_loss + lambda_sparse * sparse + lambda_close * close
        loss.backward()
        optimizer.step()
        if loss.item() < best_loss:
            best_loss  = loss.item()
            best_delta = delta.detach().clone()

    with torch.no_grad():
        cf_concepts = torch.clamp(concepts + best_delta, 0.0, 1.0)
        cf_pred     = model.predict_from_concepts(cf_concepts).argmax(dim=1).item()

    return (concepts.squeeze().cpu().numpy(),
            cf_concepts.squeeze().cpu().numpy(),
            best_delta.squeeze().cpu().numpy(),
            cf_pred)

healthy_indices = [i for i, n in enumerate(class_names) if "healthy" in n.lower()]
healthy_class   = healthy_indices[0] if healthy_indices else 0

diseased_mask    = torch.tensor(["healthy" not in class_names[t].lower() for t in all_targets])
diseased_indices = diseased_mask.nonzero(as_tuple=True)[0]

n_examples = min(3, len(diseased_indices))
fig, axes  = plt.subplots(n_examples, 1, figsize=(14, 5 * n_examples))
if n_examples == 1:
    axes = [axes]

for i in range(n_examples):
    idx           = diseased_indices[i].item()
    orig_class    = all_targets[idx].item()
    orig_concepts = all_concepts[idx]

    orig_np, cf_np, delta_np, cf_pred = generate_counterfactual(
        model, orig_concepts, orig_class, healthy_class
    )

    ax = axes[i]
    x  = np.arange(NUM_CONCEPTS)
    w  = 0.35

    ax.bar(x - w/2, orig_np, w, label=f"Original: {short_names[orig_class]}",
           color="#E74C3C", alpha=0.85)
    ax.bar(x + w/2, cf_np,   w, label=f"Counterfactual: {short_names[cf_pred]}",
           color="#2ECC71", alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(CONCEPT_NAMES, rotation=45, ha="right", fontsize=9)
    ax.set_ylim(0, 1.2)
    ax.set_ylabel("Concept Score", fontsize=11)
    ax.legend(fontsize=10)
    ax.set_title(f"Counterfactual Example {i+1}: "
                 f"{short_names[orig_class]} → {short_names[cf_pred]}", fontsize=12)
    ax.axhline(0.5, color="gray", linestyle="--", alpha=0.4)

    for j, d in enumerate(delta_np):
        if abs(d) > 0.15:
            ax.annotate(f"Δ{d:+.2f}", xy=(j + w/2, cf_np[j] + 0.05),
                        ha="center", fontsize=8, color="darkgreen", fontweight="bold")

plt.suptitle("Counterfactual Explanations — Disease to Healthy",
             fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/xai_fig1_counterfactuals.png", dpi=150, bbox_inches="tight")
plt.close()
print("✅ Counterfactual figure saved")

# =============================================================
# 2. FAITHFULNESS EVALUATION
# =============================================================
print("\n[2/4] Computing faithfulness metrics...")

def insertion_deletion_auc(model, concepts, targets, device):
    model.eval()
    importance = concepts.mean(dim=0)
    sorted_idx = importance.argsort(descending=True)
    K          = NUM_CONCEPTS
    ins_accs   = []
    del_accs   = []

    with torch.no_grad():
        for step in range(K + 1):
            ins = torch.zeros_like(concepts)
            for j in range(step):
                ins[:, sorted_idx[j]] = concepts[:, sorted_idx[j]]
            preds = model.predict_from_concepts(ins.to(device)).argmax(dim=1).cpu()
            ins_accs.append((preds == targets).float().mean().item())

            del_ = concepts.clone()
            for j in range(step):
                del_[:, sorted_idx[j]] = 0.0
            preds = model.predict_from_concepts(del_.to(device)).argmax(dim=1).cpu()
            del_accs.append((preds == targets).float().mean().item())

    x       = np.linspace(0, 1, K + 1)
    ins_auc = np.trapezoid(ins_accs, x)
    del_auc = np.trapezoid(del_accs, x)
    return ins_accs, del_accs, ins_auc, del_auc, x.tolist()

ins_accs, del_accs, ins_auc, del_auc, x = insertion_deletion_auc(
    model, all_concepts, all_targets, device
)

print(f"  Insertion AUC : {ins_auc:.4f}")
print(f"  Deletion AUC  : {del_auc:.4f}")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

ax1.plot(x, ins_accs, "b-o", linewidth=2.5, markersize=8,
         label=f"CBM Insertion (AUC={ins_auc:.3f})")
ax1.fill_between(x, ins_accs, alpha=0.15, color="blue")
ax1.set_xlabel("Fraction of concepts revealed", fontsize=12)
ax1.set_ylabel("Classification Accuracy", fontsize=12)
ax1.set_title("Insertion Curve (↑ Higher is Better)", fontsize=13, fontweight="bold")
ax1.legend(fontsize=11)
ax1.grid(alpha=0.3)
ax1.set_ylim(0, 1.05)

ax2.plot(x, del_accs, "r-o", linewidth=2.5, markersize=8,
         label=f"CBM Deletion (AUC={del_auc:.3f})")
ax2.fill_between(x, del_accs, alpha=0.15, color="red")
ax2.set_xlabel("Fraction of concepts removed", fontsize=12)
ax2.set_ylabel("Classification Accuracy", fontsize=12)
ax2.set_title("Deletion Curve (↓ Lower is Better)", fontsize=13, fontweight="bold")
ax2.legend(fontsize=11)
ax2.grid(alpha=0.3)
ax2.set_ylim(0, 1.05)

plt.suptitle("XAI Faithfulness Evaluation — Concept Bottleneck Model",
             fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/xai_fig2_faithfulness.png", dpi=150, bbox_inches="tight")
plt.close()
print("✅ Faithfulness figure saved")

# =============================================================
# 3. CONCEPT INTERVENTION ANALYSIS
# =============================================================
print("\n[3/4] Running concept intervention analysis...")

baseline_preds = model.predict_from_concepts(
    all_concepts.to(device)
).argmax(dim=1).cpu()
baseline_acc = (baseline_preds == all_targets).float().mean().item()

intervention_results = {"baseline": baseline_acc}
for k in range(NUM_CONCEPTS):
    for val in [0.0, 1.0]:
        modified       = all_concepts.clone()
        modified[:, k] = val
        preds          = model.predict_from_concepts(modified.to(device)).argmax(dim=1).cpu()
        acc            = (preds == all_targets).float().mean().item()
        intervention_results[f"{CONCEPT_NAMES[k]}={int(val)}"] = acc

fig, ax = plt.subplots(figsize=(16, 7))
keys    = [f"{n}=0" for n in CONCEPT_NAMES] + [f"{n}=1" for n in CONCEPT_NAMES]
values  = [intervention_results[k] for k in keys]
colors  = ["#E74C3C"] * NUM_CONCEPTS + ["#2ECC71"] * NUM_CONCEPTS

ax.bar(range(len(keys)), values, color=colors, alpha=0.85)
ax.axhline(baseline_acc, color="navy", linestyle="--", linewidth=2,
           label=f"Baseline Acc: {baseline_acc:.4f}")
ax.set_xticks(range(len(keys)))
ax.set_xticklabels(keys, rotation=45, ha="right", fontsize=8)
ax.set_ylabel("Accuracy after intervention", fontsize=12)
ax.set_title("Concept Intervention Analysis\n(Red = set to 0, Green = set to 1)",
             fontsize=13, fontweight="bold")
ax.set_ylim(0, 1.1)
ax.grid(axis="y", alpha=0.3)

from matplotlib.patches import Patch
ax.legend(handles=[
    Patch(facecolor="#E74C3C", alpha=0.85, label="Set concept = 0 (absent)"),
    Patch(facecolor="#2ECC71", alpha=0.85, label="Set concept = 1 (present)"),
    plt.Line2D([0], [0], color="navy", linestyle="--", linewidth=2,
               label=f"Baseline: {baseline_acc:.4f}")
], fontsize=10)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/xai_fig3_intervention.png", dpi=150, bbox_inches="tight")
plt.close()
print("✅ Intervention figure saved")

# =============================================================
# 4. CONCEPT IMPORTANCE RANKING
# =============================================================
print("\n[4/4] Computing concept importance...")

concept_importance = all_concepts.mean(dim=0).numpy()
sorted_idx         = np.argsort(concept_importance)[::-1]

fig, ax = plt.subplots(figsize=(12, 6))
colors  = plt.cm.RdYlGn(np.linspace(0.3, 0.9, NUM_CONCEPTS))
bars    = ax.bar(range(NUM_CONCEPTS),
                 concept_importance[sorted_idx],
                 color=colors, alpha=0.9, edgecolor="black", linewidth=0.5)
ax.set_xticks(range(NUM_CONCEPTS))
ax.set_xticklabels([CONCEPT_NAMES[i] for i in sorted_idx],
                   rotation=45, ha="right", fontsize=10)
ax.set_ylabel("Mean Activation Score", fontsize=12)
ax.set_title("Concept Importance Ranking\n(Mean activation across all validation samples)",
             fontsize=13, fontweight="bold")
ax.grid(axis="y", alpha=0.3)

for i, (bar, val) in enumerate(zip(bars, concept_importance[sorted_idx])):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.005,
            f"{val:.3f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/xai_fig4_concept_importance.png", dpi=150, bbox_inches="tight")
plt.close()
print("✅ Concept importance figure saved")

# =============================================================
# SUMMARY
# =============================================================
print(f"\n{'='*50}")
print("XAI RESULTS SUMMARY")
print(f"{'='*50}")
print(f"Insertion AUC     : {ins_auc:.4f}")
print(f"Deletion AUC      : {del_auc:.4f}")
print(f"Baseline Accuracy : {baseline_acc:.4f}")
print(f"\nTop 3 most important concepts:")
for i in range(3):
    idx = sorted_idx[i]
    print(f"  {i+1}. {CONCEPT_NAMES[idx]:25s} : {concept_importance[idx]:.4f}")
print(f"\n{'='*50}")
print("ALL XAI FIGURES SAVED to outputs/xai/")
print("  xai_fig1 — Counterfactual Explanations")
print("  xai_fig2 — Faithfulness (Insertion/Deletion)")
print("  xai_fig3 — Concept Intervention Analysis")
print("  xai_fig4 — Concept Importance Ranking")
print(f"{'='*50}")
print("\n✅ XAI evaluation complete!")