import os
import torch
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import albumentations as A
from albumentations.pytorch import ToTensorV2
from torch.utils.data import Dataset, DataLoader, ConcatDataset

CONCEPT_NAMES = [
    "lesion_color", "lesion_shape", "lesion_spread", "necrosis",
    "chlorosis", "wilting", "spotting", "blight_pattern",
    "mold_presence", "leaf_curl", "vein_discoloration", "lesion_texture",
]

def get_concept_labels_from_class(class_name: str) -> List[int]:
    c = [0] * 12
    name = class_name.lower()
    if any(k in name for k in ["blight", "spot", "mold", "mosaic", "curl"]): c[0] = 1
    if any(k in name for k in ["spot", "septoria", "target"]): c[1] = 1
    if any(k in name for k in ["blight", "mold"]): c[2] = 1
    if any(k in name for k in ["blight", "bacterial", "septoria"]): c[3] = 1
    if any(k in name for k in ["yellow", "mosaic", "mites"]): c[4] = 1
    if "late_blight" in name or "bacterial" in name: c[5] = 1
    if "spot" in name or "septoria" in name or "target" in name: c[6] = 1
    if "blight" in name: c[7] = 1
    if "mold" in name: c[8] = 1
    if "curl" in name or "mosaic" in name or "mites" in name: c[9] = 1
    if any(k in name for k in ["mosaic", "curl", "bacterial"]): c[10] = 1
    if any(k in name for k in ["target", "septoria", "early_blight"]): c[11] = 1
    if "healthy" in name: c = [0] * 12
    return c

def get_train_transforms(img_size: int = 224) -> A.Compose:
    return A.Compose([
        A.RandomResizedCrop(size=(img_size, img_size), scale=(0.6, 1.0)),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.3),
        A.RandomRotate90(p=0.5),
        A.OneOf([
            A.RandomBrightnessContrast(brightness_limit=0.3, contrast_limit=0.3),
            A.HueSaturationValue(hue_shift_limit=20, sat_shift_limit=30),
            A.CLAHE(clip_limit=4.0),
        ], p=0.7),
        A.OneOf([
            A.GaussianBlur(blur_limit=5),
            A.MotionBlur(blur_limit=5),
            A.MedianBlur(blur_limit=5),
        ], p=0.3),
        A.GaussNoise(p=0.3),
        A.CoarseDropout(num_holes_range=(1, 8), hole_height_range=(1, 32), hole_width_range=(1, 32), p=0.3),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2(),
    ])

def get_val_transforms(img_size: int = 224) -> A.Compose:
    return A.Compose([
        A.Resize(256, 256),
        A.CenterCrop(img_size, img_size),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2(),
    ])

class PlantDiseaseDataset(Dataset):
    def __init__(self, root_dir: str, transform=None,
                 split: str = "train", val_split: float = 0.15,
                 test_split: float = 0.15, seed: int = 42):
        self.root_dir = Path(root_dir)
        self.transform = transform
        self.samples, self.class_to_idx = self._discover_samples()

        rng = np.random.RandomState(seed)
        indices = rng.permutation(len(self.samples))
        n = len(indices)
        n_test = int(n * test_split)
        n_val = int(n * val_split)

        if split == "test":
            selected = indices[:n_test]
        elif split == "val":
            selected = indices[n_test:n_test + n_val]
        else:
            selected = indices[n_test + n_val:]

        self.samples = [self.samples[i] for i in selected]
        print(f"[{split.upper():5s}] {self.root_dir.name}: {len(self.samples)} images, {len(self.class_to_idx)} classes")

    def _discover_samples(self):
        extensions = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}
        class_to_idx = {}
        samples = []

        dirs = sorted([d for d in self.root_dir.iterdir() if d.is_dir()])
        for cls_dir in dirs:
            cls_name = cls_dir.name
            if cls_name not in class_to_idx:
                class_to_idx[cls_name] = len(class_to_idx)
            label = class_to_idx[cls_name]
            for img_path in cls_dir.rglob("*"):
                if img_path.suffix in extensions:
                    samples.append((img_path, label, cls_name))

        return samples, class_to_idx

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label, class_name = self.samples[idx]
        image = np.array(Image.open(img_path).convert("RGB"))
        if self.transform:
            augmented = self.transform(image=image)
            image = augmented["image"]
        concepts = get_concept_labels_from_class(class_name)
        return {
            "image": image,
            "label": torch.tensor(label, dtype=torch.long),
            "concepts": torch.tensor(concepts, dtype=torch.float32),
            "class_name": class_name,
        }

def get_dataloaders(plantvillage_dir: str, plantdoc_dir: str,
                    batch_size: int = 32, img_size: int = 224,
                    num_workers: int = 0):

    train_tf = get_train_transforms(img_size)
    val_tf   = get_val_transforms(img_size)

    pv_train = PlantDiseaseDataset(plantvillage_dir, train_tf, split="train")
    pv_val   = PlantDiseaseDataset(plantvillage_dir, val_tf,   split="val")
    pv_test  = PlantDiseaseDataset(plantvillage_dir, val_tf,   split="test")

    num_classes = len(pv_train.class_to_idx)
    print(f"\nTotal classes: {num_classes}")

    pd_path = Path(plantdoc_dir)
    train_root = pd_path / "train" if (pd_path / "train").exists() else pd_path
    test_root  = pd_path / "test"  if (pd_path / "test").exists()  else pd_path

    pd_train = PlantDiseaseDataset(str(train_root), train_tf, split="train")
    pd_test  = PlantDiseaseDataset(str(test_root),  val_tf,   split="train")

    combined_train = ConcatDataset([pv_train, pd_train])
    combined_test  = ConcatDataset([pv_test,  pd_test])

    return {
        "train": DataLoader(combined_train, batch_size=batch_size, shuffle=True,
                            num_workers=num_workers, pin_memory=True, drop_last=True),
        "val":   DataLoader(pv_val, batch_size=batch_size, shuffle=False,
                            num_workers=num_workers, pin_memory=True),
        "test":  DataLoader(combined_test, batch_size=batch_size, shuffle=False,
                            num_workers=num_workers, pin_memory=True),
        "test_field": DataLoader(pd_test, batch_size=batch_size, shuffle=False,
                                 num_workers=num_workers, pin_memory=True),
        "num_classes": num_classes,
    }, num_classes

if __name__ == "__main__":
    loaders, num_classes = get_dataloaders(
        plantvillage_dir="data/plantvillage/plantvillage dataset/color",
        plantdoc_dir="data/plantdoc/PlantDoc-Dataset",
    )
    batch = next(iter(loaders["train"]))
    print(f"Image shape   : {batch['image'].shape}")
    print(f"Labels shape  : {batch['label'].shape}")
    print(f"Concepts shape: {batch['concepts'].shape}")
    print(f"Num classes   : {num_classes}")
    print("✅ dataset.py works!")