import torch
import torch.nn as nn
import torch.nn.functional as F
import timm
from typing import Dict, Tuple, Optional

CONCEPT_NAMES = [
    "lesion_color", "lesion_shape", "lesion_spread", "necrosis",
    "chlorosis", "wilting", "spotting", "blight_pattern",
    "mold_presence", "leaf_curl", "vein_discoloration", "lesion_texture",
]
NUM_CONCEPTS = len(CONCEPT_NAMES)

class SEBlock(nn.Module):
    def __init__(self, channels: int, reduction: int = 16):
        super().__init__()
        self.excitation = nn.Sequential(
            nn.Linear(channels, channels // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channels // reduction, channels, bias=False),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.dim() == 4:
            B, H, W, C = x.shape
            s = x.mean(dim=[1, 2])
            scale = self.excitation(s).unsqueeze(1).unsqueeze(1)
        else:
            B, N, C = x.shape
            s = x.mean(dim=1)
            scale = self.excitation(s).unsqueeze(1)
        return x * scale

class ConceptBottleneckHead(nn.Module):
    def __init__(self, in_features: int, num_concepts: int = NUM_CONCEPTS, dropout: float = 0.3):
        super().__init__()
        self.concept_layers = nn.ModuleList([
            nn.Sequential(
                nn.Linear(in_features, 256),
                nn.BatchNorm1d(256),
                nn.ReLU(inplace=True),
                nn.Dropout(dropout),
                nn.Linear(256, 1),
                nn.Sigmoid()
            )
            for _ in range(num_concepts)
        ])
        self.num_concepts = num_concepts

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.cat([layer(x) for layer in self.concept_layers], dim=1)

class ConceptClassifier(nn.Module):
    def __init__(self, num_concepts: int = NUM_CONCEPTS, num_classes: int = 38, dropout: float = 0.2):
        super().__init__()
        self.classifier = nn.Sequential(
            nn.Linear(num_concepts, 64),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(64, num_classes)
        )

    def forward(self, concepts: torch.Tensor) -> torch.Tensor:
        return self.classifier(concepts)

class PlantDiseaseCBM(nn.Module):
    def __init__(self, num_classes: int = 38, num_concepts: int = NUM_CONCEPTS,
                 pretrained: bool = True, dropout: float = 0.3, se_reduction: int = 16):
        super().__init__()
        self.backbone = timm.create_model(
            "swin_small_patch4_window7_224",
            pretrained=pretrained,
            num_classes=0,
            global_pool=""
        )
        backbone_dim = self.backbone.num_features
        self.se_block = SEBlock(channels=backbone_dim, reduction=se_reduction)
        self.gap = nn.AdaptiveAvgPool2d(1)
        self.concept_head = ConceptBottleneckHead(backbone_dim, num_concepts, dropout)
        self.classifier = ConceptClassifier(num_concepts, num_classes, dropout)
        self.num_classes = num_classes
        self.num_concepts = num_concepts
        self.backbone_dim = backbone_dim

    def forward_features(self, x: torch.Tensor) -> torch.Tensor:
        feats = self.backbone(x)        # (B, H, W, C)
        feats = self.se_block(feats)    # (B, H, W, C)
        feats = feats.permute(0, 3, 1, 2)  # (B, C, H, W)
        feats = self.gap(feats)         # (B, C, 1, 1)
        feats = feats.squeeze(-1).squeeze(-1)  # (B, C)
        return feats

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        features = self.forward_features(x)
        concepts = self.concept_head(features)
        logits = self.classifier(concepts)
        return logits, concepts, features

    def predict_from_concepts(self, concepts: torch.Tensor) -> torch.Tensor:
        return self.classifier(concepts)

    def get_concept_names(self):
        return CONCEPT_NAMES

class CBMLoss(nn.Module):
    def __init__(self, lambda_task=1.0, lambda_concept=0.5, lambda_diversity=0.1):
        super().__init__()
        self.lambda_task = lambda_task
        self.lambda_concept = lambda_concept
        self.lambda_diversity = lambda_diversity
        self.task_loss = nn.CrossEntropyLoss()
        self.concept_loss = nn.BCELoss()

    def diversity_loss(self, concepts: torch.Tensor) -> torch.Tensor:
        c = F.normalize(concepts, dim=0)
        corr = torch.mm(c.T, c) / concepts.shape[0]
        mask = 1 - torch.eye(corr.shape[0], device=corr.device)
        return (corr * mask).abs().mean()

    def forward(self, logits, targets, concepts, concept_labels=None):
        l_task = self.task_loss(logits, targets)
        l_concept = self.concept_loss(concepts, concept_labels.float()) if concept_labels is not None else torch.tensor(0.0, device=logits.device)
        l_div = self.diversity_loss(concepts)
        total = self.lambda_task * l_task + self.lambda_concept * l_concept + self.lambda_diversity * l_div
        return {"total": total, "task": l_task, "concept": l_concept, "diversity": l_div}

if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    model = PlantDiseaseCBM(num_classes=38, pretrained=False).to(device)
    x = torch.randn(4, 3, 224, 224).to(device)
    logits, concepts, features = model(x)
    print(f"Logits  : {logits.shape}")
    print(f"Concepts: {concepts.shape}")
    print(f"Features: {features.shape}")
    print("✅ model.py works!")