import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import torch
import time
import numpy as np
from pathlib import Path
from sklearn.metrics import accuracy_score
from model import PlantDiseaseCBM, NUM_CONCEPTS
from dataset import get_dataloaders

PLANTVILLAGE_DIR = "data/plantvillage/plantvillage dataset/color"
PLANTDOC_DIR     = "data/plantdoc/PlantDoc-Dataset"
CHECKPOINT       = "outputs/checkpoints/best_model.pth"
OUTPUT_DIR       = "outputs/checkpoints"

device = torch.device("cpu")  # Quantization runs on CPU
print("Loading model...")
ckpt        = torch.load(CHECKPOINT, map_location=device)
num_classes = ckpt["num_classes"]

model = PlantDiseaseCBM(
    num_classes=num_classes,
    num_concepts=NUM_CONCEPTS,
    pretrained=False
)
model.load_state_dict(ckpt["model"])
model.eval()

# ── Original model size ───────────────────────────────────
original_path = f"{OUTPUT_DIR}/model_original.pt"
torch.save(model.state_dict(), original_path)
original_size = os.path.getsize(original_path) / (1024 * 1024)
print(f"Original model size : {original_size:.2f} MB")

# ── Load data for calibration and evaluation ──────────────
print("\nLoading data...")
loaders, _ = get_dataloaders(
    PLANTVILLAGE_DIR, PLANTDOC_DIR,
    batch_size=32, num_workers=0
)

# ── Evaluate original model speed and accuracy ────────────
print("\nEvaluating original model...")
all_preds, all_targets = [], []
start = time.time()

with torch.no_grad():
    for i, batch in enumerate(loaders["val"]):
        if i >= 50:  # Test on 50 batches
            break
        images  = batch["image"]
        targets = batch["label"]
        logits, _, _ = model(images)
        preds = logits.argmax(dim=1).numpy()
        all_preds.extend(preds)
        all_targets.extend(targets.numpy())

original_time = time.time() - start
original_acc  = accuracy_score(all_targets, all_preds)
print(f"Original accuracy   : {original_acc:.4f}")
print(f"Original inference  : {original_time:.2f}s for 50 batches")

# ── Dynamic Quantization ──────────────────────────────────
print("\nApplying Dynamic Quantization (INT8)...")
quantized_model = torch.quantization.quantize_dynamic(
    model,
    {torch.nn.Linear},
    dtype=torch.qint8
)
print("✅ Quantization applied!")

# ── Quantized model size ──────────────────────────────────
quantized_path = f"{OUTPUT_DIR}/model_quantized.pt"
torch.save(quantized_model.state_dict(), quantized_path)
quantized_size = os.path.getsize(quantized_path) / (1024 * 1024)
print(f"Quantized model size: {quantized_size:.2f} MB")

# ── Evaluate quantized model ──────────────────────────────
print("\nEvaluating quantized model...")
all_preds_q, all_targets_q = [], []
start = time.time()

with torch.no_grad():
    for i, batch in enumerate(loaders["val"]):
        if i >= 50:
            break
        images  = batch["image"]
        targets = batch["label"]
        logits, _, _ = quantized_model(images)
        preds = logits.argmax(dim=1).numpy()
        all_preds_q.extend(preds)
        all_targets_q.extend(targets.numpy())

quantized_time = time.time() - start
quantized_acc  = accuracy_score(all_targets_q, all_preds_q)
print(f"Quantized accuracy  : {quantized_acc:.4f}")
print(f"Quantized inference : {quantized_time:.2f}s for 50 batches")

# ── Summary ───────────────────────────────────────────────
size_reduction  = (1 - quantized_size / original_size) * 100
acc_drop        = (original_acc - quantized_acc) * 100
speedup         = original_time / quantized_time

print(f"\n{'='*50}")
print("QUANTIZATION RESULTS SUMMARY")
print(f"{'='*50}")
print(f"Original size    : {original_size:.2f} MB")
print(f"Quantized size   : {quantized_size:.2f} MB")
print(f"Size reduction   : {size_reduction:.1f}%")
print(f"Original acc     : {original_acc*100:.2f}%")
print(f"Quantized acc    : {quantized_acc*100:.2f}%")
print(f"Accuracy drop    : {acc_drop:.2f}%")
print(f"Speedup          : {speedup:.2f}x faster")
print(f"{'='*50}")
print("\n✅ Quantization complete!")
print(f"Quantized model saved: {quantized_path}")