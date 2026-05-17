import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts
from torch.utils.tensorboard import SummaryWriter
import numpy as np
from sklearn.metrics import accuracy_score, f1_score
from pathlib import Path
import json

from model import PlantDiseaseCBM, CBMLoss, NUM_CONCEPTS
from dataset import get_dataloaders

# ── Config ────────────────────────────────────────────────
PLANTVILLAGE_DIR = "data/plantvillage/plantvillage dataset/color"
PLANTDOC_DIR     = "data/plantdoc/PlantDoc-Dataset"
OUTPUT_DIR       = "outputs/checkpoints"
EPOCHS           = 100
BATCH_SIZE       = 32
LR               = 1e-4
WARMUP_EPOCHS    = 5
SEED             = 42

def set_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)

def train_epoch(model, loader, optimizer, criterion, device, writer, global_step):
    model.train()
    total_loss = 0.0
    all_preds, all_targets = [], []
    total_batches = len(loader)

    for i, batch in enumerate(loader):
        images      = batch["image"].to(device, non_blocking=True)
        targets     = batch["label"].to(device, non_blocking=True)
        concepts_gt = batch["concepts"].to(device, non_blocking=True)

        optimizer.zero_grad()
        logits, concepts, _ = model(images)
        losses = criterion(logits, targets, concepts, concepts_gt)
        losses["total"].backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += losses["total"].item()
        preds = logits.argmax(dim=1).cpu().numpy()
        all_preds.extend(preds)
        all_targets.extend(targets.cpu().numpy())
        writer.add_scalar("Loss/train", losses["total"].item(), global_step)
        global_step += 1

        if (i + 1) % 200 == 0:
            print(f"    Batch [{i+1}/{total_batches}] Loss: {losses['total'].item():.4f}")

    acc = accuracy_score(all_targets, all_preds)
    f1  = f1_score(all_targets, all_preds, average="macro", zero_division=0)
    return total_loss / len(loader), acc, f1, global_step

@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    all_preds, all_targets = [], []

    for batch in loader:
        images      = batch["image"].to(device, non_blocking=True)
        targets     = batch["label"].to(device, non_blocking=True)
        concepts_gt = batch["concepts"].to(device, non_blocking=True)
        logits, concepts, _ = model(images)
        losses = criterion(logits, targets, concepts, concepts_gt)
        total_loss += losses["total"].item()
        preds = logits.argmax(dim=1).cpu().numpy()
        all_preds.extend(preds)
        all_targets.extend(targets.cpu().numpy())

    acc = accuracy_score(all_targets, all_preds)
    f1  = f1_score(all_targets, all_preds, average="macro", zero_division=0)
    return total_loss / len(loader), acc, f1, all_preds, all_targets

def main():
    set_seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n{'='*60}")
    print(f"  Plant Disease CBM Training")
    print(f"  Device : {device}")
    if torch.cuda.is_available():
        print(f"  GPU    : {torch.cuda.get_device_name(0)}")
        print(f"  VRAM   : {torch.cuda.get_device_properties(0).total_memory/1e9:.1f} GB")
    print(f"  Epochs : {EPOCHS}")
    print(f"  Batch  : {BATCH_SIZE}")
    print(f"{'='*60}\n")

    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    writer = SummaryWriter(log_dir=str(out_dir / "tensorboard"))

    print("Loading datasets...")
    loaders, num_classes = get_dataloaders(
        plantvillage_dir=PLANTVILLAGE_DIR,
        plantdoc_dir=PLANTDOC_DIR,
        batch_size=BATCH_SIZE,
    )

    print(f"\nBuilding model with {num_classes} classes...")
    model = PlantDiseaseCBM(
        num_classes=num_classes,
        num_concepts=NUM_CONCEPTS,
        pretrained=True,
    ).to(device)

    criterion = CBMLoss(lambda_task=1.0, lambda_concept=0.5, lambda_diversity=0.1)
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    scheduler = CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2, eta_min=1e-6)

    best_val_acc = 0.0
    global_step  = 0
    history      = []

    for param in model.backbone.parameters():
        param.requires_grad = False
    print("Backbone frozen for warmup phase\n")

    for epoch in range(EPOCHS):
        if epoch == WARMUP_EPOCHS:
            for param in model.backbone.parameters():
                param.requires_grad = True
            for g in optimizer.param_groups:
                g["lr"] = LR * 0.1
            print("Backbone unfrozen — full model training\n")

        print(f"\nEpoch [{epoch+1}/{EPOCHS}] Training...")
        train_loss, train_acc, train_f1, global_step = train_epoch(
            model, loaders["train"], optimizer, criterion, device, writer, global_step
        )

        print(f"Epoch [{epoch+1}/{EPOCHS}] Evaluating...")
        val_loss, val_acc, val_f1, _, _ = evaluate(
            model, loaders["val"], criterion, device
        )
        scheduler.step()

        print(
            f"Epoch [{epoch+1:03d}/{EPOCHS}] "
            f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} F1: {train_f1:.4f} | "
            f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f} F1: {val_f1:.4f}"
        )

        writer.add_scalars("Accuracy", {"train": train_acc, "val": val_acc}, epoch)
        writer.add_scalar("LR", optimizer.param_groups[0]["lr"], epoch)

        history.append({
            "epoch": epoch + 1,
            "train_acc": train_acc, "train_f1": train_f1,
            "val_acc": val_acc,     "val_f1": val_f1,
        })

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                "epoch": epoch,
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "best_val_acc": best_val_acc,
                "num_classes": num_classes,
            }, out_dir / "best_model.pth")
            print(f"  ✅ Best model saved! Val acc: {best_val_acc:.4f}")

        torch.save({
            "epoch": epoch,
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "best_val_acc": best_val_acc,
            "num_classes": num_classes,
        }, out_dir / "last_model.pth")

    print(f"\n{'='*60}")
    print("FINAL TEST EVALUATION")
    print(f"{'='*60}")
    ckpt = torch.load(out_dir / "best_model.pth", map_location=device)
    model.load_state_dict(ckpt["model"])
    test_loss, test_acc, test_f1, preds, targets = evaluate(
        model, loaders["test"], criterion, device
    )
    print(f"Test Acc: {test_acc:.4f}  F1: {test_f1:.4f}")

    with open(out_dir / "results.json", "w") as f:
        json.dump({
            "best_val_acc": best_val_acc,
            "test_acc": test_acc,
            "test_f1": test_f1,
            "history": history
        }, f, indent=2)

    writer.close()
    print(f"\n✅ Training complete! Best val acc: {best_val_acc:.4f}")

if __name__ == "__main__":
    main()