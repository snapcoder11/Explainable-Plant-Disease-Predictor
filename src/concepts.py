import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import torch
import numpy as np
from model import PlantDiseaseCBM, NUM_CONCEPTS, CONCEPT_NAMES
from dataset import PlantDiseaseDataset, get_val_transforms

PLANTVILLAGE_DIR = "data/plantvillage/plantvillage dataset/color"
CHECKPOINT       = "outputs/checkpoints/best_model.pth"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load model
ckpt        = torch.load(CHECKPOINT, map_location=device)
num_classes = ckpt["num_classes"]
model       = PlantDiseaseCBM(num_classes=num_classes, num_concepts=NUM_CONCEPTS, pretrained=False).to(device)
model.load_state_dict(ckpt["model"])
model.eval()

# Load dataset
dataset     = PlantDiseaseDataset(PLANTVILLAGE_DIR, get_val_transforms(), split="val")
idx_to_class = {v: k for k, v in dataset.class_to_idx.items()}

# Target classes to show
targets = [
    "Peach___Bacterial_spot",
    "Tomato___Target_Spot",
    "Grape___Black_rot",
    "Tomato___Late_blight",
    "Apple___Apple_scab",
    "Apple___healthy",
    "Tomato___healthy",
]

# Find one sample per class
selected = {}
for img_path, label, cls in dataset.samples:
    if cls in targets and cls not in selected:
        selected[cls] = (img_path, label, cls)
    if len(selected) == len(targets):
        break

# Run inference
with torch.no_grad():
    for cls_name, (img_path, true_label, _) in selected.items():

        # Get sample directly
        idx = next(i for i,(p,l,c) in enumerate(dataset.samples) if p==img_path)
        sample  = dataset[idx]
        image   = sample["image"].unsqueeze(0).to(device)

        logits, concepts, _ = model(image)
        pred_label     = logits.argmax(dim=1).item()
        concept_scores = concepts.squeeze().cpu().numpy()
        pred_name      = idx_to_class.get(pred_label, str(pred_label))
        correct        = "✅" if pred_label == true_label else "❌"

        print(f"\n{'='*60}")
        print(f"  TRUE  : {cls_name}")
        print(f"  PRED  : {pred_name}  {correct}")
        print(f"{'='*60}")
        print(f"  {'CONCEPT':<22} {'SCORE':>6}  BAR")
        print(f"  {'-'*55}")

        for ci in np.argsort(concept_scores)[::-1]:
            name  = CONCEPT_NAMES[ci]
            score = concept_scores[ci]
            bar   = "█" * int(score * 25) + "░" * (25 - int(score * 25))
            level = "HIGH" if score >= 0.7 else "MED " if score >= 0.3 else "low "
            print(f"  {name:<22} {score:>6.3f}  [{bar}] {level}")