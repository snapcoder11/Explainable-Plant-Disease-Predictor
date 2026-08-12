"""
Generate PowerPoint presentation for PlantDiseaseCBM URE project
Author: Anushka Mahraniya | 20221CSD0151
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import os

BASE = r"c:\Users\Anushka Mahraniya\Desktop\PlantDisease"
FIG  = os.path.join(BASE, "outputs", "figures")
XAI  = os.path.join(BASE, "outputs", "xai")
APP  = os.path.join(BASE, "outputs", "appendix")

# ── Colour palette ─────────────────────────────────────────────
DARK_BG   = RGBColor(0x0D, 0x1B, 0x2A)   # deep navy
ACCENT    = RGBColor(0x2E, 0xCC, 0x71)   # green
ACCENT2   = RGBColor(0x27, 0xAE, 0x60)   # darker green
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_TXT = RGBColor(0xCC, 0xDD, 0xEE)
CARD_BG   = RGBColor(0x15, 0x2B, 0x3E)   # slightly lighter navy
YELLOW    = RGBColor(0xF3, 0x9C, 0x12)

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)

BLANK = prs.slide_layouts[6]   # completely blank

# ── Helpers ────────────────────────────────────────────────────
def bg(slide, color=DARK_BG):
    from pptx.oxml.ns import qn
    from lxml import etree
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color

def box(slide, left, top, width, height, color, alpha=None):
    shape = slide.shapes.add_shape(1, Inches(left), Inches(top), Inches(width), Inches(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape

def txt(slide, text, left, top, width, height,
        size=18, bold=False, color=WHITE, align=PP_ALIGN.LEFT,
        italic=False, wrap=True):
    txb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    txb.word_wrap = wrap
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = "Calibri"
    return txb

def txt_lines(slide, lines, left, top, width, height,
              size=16, color=WHITE, bold=False, spacing=1.15):
    txb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True
    first = True
    for line in lines:
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        p.space_before = Pt(4)
        run = p.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
        run.font.name = "Calibri"

def bullet_box(slide, items, left, top, width, height, size=16, color=WHITE, dot_color=ACCENT):
    txb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True
    first = True
    for item in items:
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        p.space_before = Pt(5)
        dot = p.add_run()
        dot.text = "● "
        dot.font.size = Pt(size)
        dot.font.color.rgb = dot_color
        dot.font.name = "Calibri"
        run = p.add_run()
        run.text = item
        run.font.size = Pt(size)
        run.font.color.rgb = color
        run.font.name = "Calibri"

def card(slide, left, top, w, h, title, value, title_size=13, val_size=22):
    box(slide, left, top, w, h, CARD_BG)
    box(slide, left, top, w, 0.04, ACCENT)
    txt(slide, title, left+0.12, top+0.1, w-0.2, 0.35,
        size=title_size, color=LIGHT_TXT, bold=False)
    txt(slide, value, left+0.12, top+0.42, w-0.2, h-0.55,
        size=val_size, color=ACCENT, bold=True)

def add_img(slide, path, left, top, width=None, height=None):
    if not os.path.exists(path):
        return
    if width and height:
        slide.shapes.add_picture(path, Inches(left), Inches(top), Inches(width), Inches(height))
    elif width:
        slide.shapes.add_picture(path, Inches(left), Inches(top), width=Inches(width))
    else:
        slide.shapes.add_picture(path, Inches(left), Inches(top), height=Inches(height))

def accent_bar(slide, top=0.72):
    box(slide, 0, top, 13.33, 0.06, ACCENT)

def slide_header(slide, title, subtitle=None):
    accent_bar(slide, top=0)
    box(slide, 0, 0, 13.33, 1.15, DARK_BG)
    txt(slide, title, 0.4, 0.1, 10, 0.65, size=30, bold=True, color=WHITE)
    if subtitle:
        txt(slide, subtitle, 0.4, 0.72, 10, 0.38, size=16, color=ACCENT)
    accent_bar(slide, top=1.1)

def footer(slide, text="Anushka Mahraniya | 20221CSD0151 | Presidency University"):
    box(slide, 0, 7.2, 13.33, 0.3, RGBColor(0x08, 0x12, 0x1C))
    txt(slide, text, 0.2, 7.2, 13, 0.3, size=11, color=LIGHT_TXT)


# =============================================================
# SLIDE 1 — TITLE
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
box(sl, 0, 0, 13.33, 7.5, DARK_BG)
box(sl, 0, 0, 0.12, 7.5, ACCENT)
box(sl, 0, 3.6, 13.33, 0.06, ACCENT)

txt(sl, "EXPLAINABLE PLANT DISEASE DETECTION",
    0.5, 0.6, 12.5, 1.0, size=34, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
txt(sl, "via Concept Bottleneck Modelling with Swin Transformer Backbone",
    0.5, 1.55, 12.5, 0.7, size=20, color=ACCENT, align=PP_ALIGN.CENTER)

box(sl, 1.5, 2.5, 10.33, 1.0, CARD_BG)
txt(sl, "URE Research Presentation", 1.5, 2.55, 10.33, 0.5,
    size=17, color=LIGHT_TXT, align=PP_ALIGN.CENTER)

txt(sl, "Anushka Mahraniya",        0.5, 3.8,  12.5, 0.5, size=22, bold=True,  color=WHITE,     align=PP_ALIGN.CENTER)
txt(sl, "USN: 20221CSD0151",        0.5, 4.28, 12.5, 0.4, size=16, color=LIGHT_TXT, align=PP_ALIGN.CENTER)
txt(sl, "Guide: Meena Kumari K S",  0.5, 4.65, 12.5, 0.4, size=16, color=LIGHT_TXT, align=PP_ALIGN.CENTER)
txt(sl, "Presidency University, Bengaluru | B.Tech CSE (Data Science) | April 2026",
    0.5, 5.05, 12.5, 0.4, size=14, color=LIGHT_TXT, align=PP_ALIGN.CENTER)

box(sl, 0.5, 5.65, 12.33, 0.06, ACCENT2)
txt(sl, "PlantVillage + PlantDoc  ●  38 Disease Classes  ●  99.91% Accuracy  ●  Deployed on Hugging Face",
    0.5, 5.75, 12.5, 0.5, size=14, color=ACCENT, align=PP_ALIGN.CENTER)


# =============================================================
# SLIDE 2 — THE PROBLEM
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
slide_header(sl, "The Problem", "Why do we need better plant disease detection?")
footer(sl)

box(sl, 0.3, 1.3, 12.7, 5.6, CARD_BG)

txt(sl, "🌿  Plant diseases destroy 20–40% of global crop yield every year",
    0.6, 1.5, 12, 0.5, size=18, color=WHITE, bold=True)

issues = [
    ("❌  Current AI models are Black Boxes",
     "Farmers get a prediction but no explanation — they don't know WHY the model said what it said."),
    ("❌  Lab images ≠ Real field images",
     "Models trained on clean lab photos fail when tested on real, messy, outdoor field photographs."),
    ("❌  Too heavy for field devices",
     "Large deep learning models cannot run on the phones and tablets farmers actually use."),
]

y = 2.1
for title, desc in issues:
    box(sl, 0.5, y, 12.2, 1.3, RGBColor(0x1A, 0x35, 0x4E))
    txt(sl, title, 0.7, y+0.08, 11.8, 0.45, size=17, bold=True, color=ACCENT)
    txt(sl, desc,  0.7, y+0.5,  11.8, 0.7,  size=15, color=LIGHT_TXT)
    y += 1.45


# =============================================================
# SLIDE 3 — SOLUTION OVERVIEW
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
slide_header(sl, "Our Solution — PlantDiseaseCBM", "One model. Three problems solved.")
footer(sl)

solutions = [
    ("🧠  Explainability",    "Concept Bottleneck Model\nexplains predictions using\n12 biological symptoms"),
    ("🌿  Generalisation",    "Trained on PlantVillage +\nPlantDoc (real field photos)\nfor real-world robustness"),
    ("⚡  Deployment",        "INT8 Quantisation makes\nthe model 23% smaller &\n1.3× faster on CPU"),
    ("🔬  XAI Analysis",      "4 explanation tools:\ncounterfactuals, faithfulness,\nintervention, importance"),
]

x = 0.35
for icon_title, desc in solutions:
    box(sl, x, 1.4, 2.9, 5.2, CARD_BG)
    box(sl, x, 1.4, 2.9, 0.06, ACCENT)
    txt(sl, icon_title, x+0.1, 1.5,  2.7, 0.6, size=17, bold=True, color=ACCENT)
    txt(sl, desc,       x+0.1, 2.15, 2.7, 4.2, size=15, color=WHITE)
    x += 3.18


# =============================================================
# SLIDE 4 — DATASET
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
slide_header(sl, "Dataset", "What data was the model trained on?")
footer(sl)

box(sl, 0.3, 1.3, 6.1, 5.4, CARD_BG)
txt(sl, "🗂  PlantVillage", 0.5, 1.4, 5.8, 0.5, size=20, bold=True, color=ACCENT)
bullet_box(sl, [
    "54,306 colour leaf images",
    "38 disease-species classes",
    "14 crop species (Apple, Tomato,\n   Corn, Grape, Potato…)",
    "Controlled lab background",
    "Split: 70% train / 15% val / 15% test",
], 0.5, 1.95, 5.7, 4.5, size=16)

box(sl, 6.9, 1.3, 6.1, 5.4, CARD_BG)
txt(sl, "🌾  PlantDoc (Field Images)", 7.1, 1.4, 5.8, 0.5, size=20, bold=True, color=YELLOW)
bullet_box(sl, [
    "2,598 real field photographs",
    "27 disease classes",
    "Natural backgrounds, variable light",
    "Multiple leaves per frame",
    "Used for out-of-distribution testing",
], 7.1, 1.95, 5.7, 4.5, size=16, dot_color=YELLOW)

add_img(sl, os.path.join(FIG, "fig4_dataset_comparison.png"), 0.35, 1.35, width=12.5)


# =============================================================
# SLIDE 5 — MODEL ARCHITECTURE
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
slide_header(sl, "Model Architecture — PlantDiseaseCBM", "How does the model work?")
footer(sl)

steps = [
    ("1", "Input Image\n224×224 px"),
    ("2", "Swin Transformer\n+ SE Attention Block"),
    ("3", "12 Concept\nBottleneck Scores"),
    ("4", "38-Class\nDisease Output"),
]

x = 0.4
for num, label in steps:
    box(sl, x, 2.0, 2.7, 2.2, CARD_BG)
    box(sl, x, 2.0, 2.7, 0.06, ACCENT)
    txt(sl, num,   x+0.1, 2.1,  2.5, 0.5, size=28, bold=True, color=ACCENT)
    txt(sl, label, x+0.1, 2.65, 2.5, 1.4, size=16, color=WHITE)
    if num != "4":
        txt(sl, "→", x+2.75, 2.85, 0.5, 0.5, size=28, bold=True, color=ACCENT)
    x += 3.2

txt(sl, "The KEY innovation: All predictions MUST pass through the 12 concept scores.",
    0.4, 4.45, 12.5, 0.5, size=17, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
txt(sl, "This means the model is forced to explain itself using biological symptoms before giving an answer.",
    0.4, 4.95, 12.5, 0.5, size=15, color=LIGHT_TXT, align=PP_ALIGN.CENTER)

add_img(sl, os.path.join(FIG, "architecture.png"), 0.4, 1.3, width=12.5)


# =============================================================
# SLIDE 5B — ALGORITHMS USED (OVERVIEW)
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
slide_header(sl, "Algorithms & Techniques Used", "Every algorithm in this project — at a glance")
footer(sl)

algo_grid = [
    ("Swin Transformer",        "Backbone",          "Hierarchical shifted-window self-attention\nfor extracting spatial disease features"),
    ("SE Block",                "Attention",          "Squeeze-and-Excitation channel recalibration\n— amplifies disease-relevant feature channels"),
    ("Concept Bottleneck (CBM)","Core Innovation",   "Forces all decisions through 12 interpretable\nbiology-based symptom scores"),
    ("Adam Optimizer",          "Optimisation",       "Adaptive learning rate optimiser\n(lr=1e-4, weight decay=1e-4)"),
    ("CBM Composite Loss",      "Loss Function",      "Task loss + Concept BCE loss +\nDiversity regularisation (λ=1.0/0.5/0.1)"),
    ("Albumentations",          "Augmentation",       "8-step pipeline: crop, flip, rotate,\ncolor jitter, blur, noise, dropout, normalise"),
    ("INT8 Dynamic Quantisation","Deployment",        "Compresses Linear layers from FP32→INT8\n23% smaller model, 1.3× faster CPU"),
    ("Counterfactual Perturb.", "XAI Method 1",       "Adam optimised over 300 iters to find\nminimum concept change to flip prediction"),
    ("Insertion-Deletion AUC",  "XAI Method 2",       "Faithfulness test: Insertion AUC=0.847\nDeletion AUC=0.312"),
    ("Concept Intervention",    "XAI Method 3",       "Hard-sets each concept to 0 or 1\nand measures accuracy change"),
    ("FastAPI + Docker",        "Serving",            "REST API endpoint for model inference\npackaged in Docker container"),
    ("Stratified Split",        "Data Strategy",      "70/15/15 train-val-test split\nwith fixed random seed=42"),
]

x_start, y_start = 0.2, 1.3
cols = 3
cw, ch = 4.2, 1.52
for i, (name, tag, desc) in enumerate(algo_grid):
    col = i % cols
    row = i // cols
    cx = x_start + col * (cw + 0.15)
    cy = y_start + row * (ch + 0.1)
    box(sl, cx, cy, cw, ch, CARD_BG)
    box(sl, cx, cy, cw, 0.05, ACCENT)
    # tag chip
    tag_box = sl.shapes.add_shape(1, Inches(cx+0.08), Inches(cy+0.1),
                                   Inches(1.5), Inches(0.32))
    tag_box.fill.solid(); tag_box.fill.fore_color.rgb = RGBColor(0x1A,0x6B,0x3C)
    tag_box.line.fill.background()
    txt(sl, tag,  cx+0.08, cy+0.1,  1.5,  0.32, size=10, color=WHITE, bold=True)
    txt(sl, name, cx+0.08, cy+0.45, cw-0.2, 0.42, size=14, bold=True, color=ACCENT)
    txt(sl, desc, cx+0.08, cy+0.88, cw-0.2, 0.6,  size=12, color=LIGHT_TXT)


# =============================================================
# SLIDE 5C — TRAINING ALGORITHM DETAIL
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
slide_header(sl, "Training Algorithm — How the Model Learns", "Step-by-step training process")
footer(sl)

# Left: Loss function breakdown
box(sl, 0.3, 1.3, 6.0, 5.5, CARD_BG)
box(sl, 0.3, 1.3, 0.06, 5.5, ACCENT)
txt(sl, "📐  Loss Function (CBMLoss)", 0.5, 1.38, 5.7, 0.5, size=17, bold=True, color=ACCENT)

loss_lines = [
    "L  =  λ_task · L_task",
    "     +  λ_concept · L_concept",
    "     +  λ_div · L_diversity",
    "",
    "λ_task    = 1.0   →  Cross-entropy (38 classes)",
    "λ_concept = 0.5   →  Binary CE per concept",
    "λ_div     = 0.1   →  Penalise concept correlation",
    "",
    "Diversity Loss prevents all 12 concepts from",
    "learning the same thing (concept collapse).",
]
txt_lines(sl, loss_lines, 0.5, 1.95, 5.7, 4.7, size=14, color=WHITE)

# Right: Training steps
box(sl, 6.6, 1.3, 6.4, 5.5, CARD_BG)
box(sl, 6.6, 1.3, 0.06, 5.5, ACCENT)
txt(sl, "⚙️  Training Configuration", 6.8, 1.38, 6.1, 0.5, size=17, bold=True, color=ACCENT)

train_rows = [
    ("Epochs",         "100"),
    ("Batch Size",     "32"),
    ("Optimizer",      "Adam (lr=1e-4)"),
    ("LR Scheduler",   "CosineAnnealingLR"),
    ("Weight Decay",   "1e-4"),
    ("Backbone",       "Swin-Small (ImageNet pretrained)"),
    ("Concept Labels", "Programmatic (keyword matching)"),
    ("Random Seed",    "42 (reproducible)"),
    ("Framework",      "PyTorch 2.1.0 + timm 0.9.7"),
    ("Augmentation",   "Albumentations 1.3.1"),
]

y = 1.95
for label, val in train_rows:
    txt(sl, label + ":", 6.8,  y, 2.5, 0.42, size=13, bold=True, color=LIGHT_TXT)
    txt(sl, val,         9.35, y, 3.5, 0.42, size=13, color=WHITE)
    y += 0.46


# =============================================================
# SLIDE 5D — SWIN TRANSFORMER: HOW IT WORKS
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
slide_header(sl, "Swin Transformer — How It Works", "The backbone that sees the entire leaf, not just a small patch")
footer(sl)

# Left column: Problem + Patch Partition
box(sl, 0.3, 1.3, 6.0, 5.5, CARD_BG)
box(sl, 0.3, 1.3, 0.06, 5.5, ACCENT)
txt(sl, "Why Swin? The Core Problem", 0.5, 1.38, 5.7, 0.48, size=16, bold=True, color=ACCENT)
txt_lines(sl, [
    "CNN (ResNet):  sees only a 3x3 patch at a time.",
    "              Cannot relate distant leaf regions.",
    "",
    "ViT:           attends to ALL patches together.",
    "              O(N2) cost — too slow for 224x224.",
    "",
    "Swin:          local windows + periodic shifts.",
    "              Captures both fine detail AND global",
    "              disease spread. O(N) cost.",
], 0.5, 1.9, 5.7, 2.6, size=13, color=WHITE)

txt(sl, "Step 1 — Patch Partition (patch size = 4)", 0.5, 4.55, 5.7, 0.42, size=14, bold=True, color=YELLOW)
txt_lines(sl, [
    "224x224 image  divided into 4x4 non-overlapping patches",
    "= 56 x 56 = 3,136 patches (tokens)",
    "Each patch: 48 raw pixel values  projected to 96-dim",
    "Result: 56 x 56 x 96 feature map",
    "Each patch is now one 'word' in a visual sentence.",
], 0.5, 5.0, 5.7, 1.7, size=12, color=LIGHT_TXT)

# Right column: Four stages
box(sl, 6.6, 1.3, 6.4, 5.5, CARD_BG)
box(sl, 6.6, 1.3, 0.06, 5.5, ACCENT)
txt(sl, "Step 2 — Four Hierarchical Stages", 6.8, 1.38, 6.1, 0.48, size=16, bold=True, color=ACCENT)
txt(sl, "Like zooming out to understand context:", 6.8, 1.9, 6.1, 0.38, size=13, color=LIGHT_TXT, italic=True)

stages = [
    ("Stage 1", "56x56x96",   "Fine detail — edges, textures, lesion surfaces"),
    ("Stage 2", "28x28x192",  "Local patterns — spot shapes, lesion boundaries"),
    ("Stage 3", "14x14x384",  "Mid-level — lesion spread, color zones"),
    ("Stage 4", "7x7x768",    "Global — whole-leaf disease pattern  (used by your model)"),
]
y = 2.38
for stage, dims, meaning in stages:
    box(sl, 6.7, y, 6.2, 1.05, RGBColor(0x1A, 0x35, 0x4E))
    txt(sl, stage, 6.85, y+0.08, 1.2, 0.4, size=13, bold=True, color=ACCENT)
    txt(sl, dims,  8.1,  y+0.08, 1.8, 0.4, size=13, bold=True, color=YELLOW)
    txt(sl, meaning, 6.85, y+0.52, 6.0, 0.45, size=12, color=WHITE)
    y += 1.15

txt(sl, "Each stage: patches merged (2x2), channels doubled. Patch merge = stride-2 like operation.",
    6.8, 6.55, 6.1, 0.45, size=11, color=LIGHT_TXT, italic=True)


# =============================================================
# SLIDE 5E — WINDOW ATTENTION & THE SHIFTED WINDOW INNOVATION
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
slide_header(sl, "Swin Transformer — The Shifted Window Innovation", "How the model connects distant leaf regions efficiently")
footer(sl)

# Left: W-MSA
box(sl, 0.3, 1.3, 6.0, 5.5, CARD_BG)
box(sl, 0.3, 1.3, 0.06, 5.5, ACCENT)
txt(sl, "Window Multi-Head Self-Attention (W-MSA)", 0.5, 1.38, 5.7, 0.48, size=15, bold=True, color=ACCENT)

txt_lines(sl, [
    "Problem: attending over all 3,136 patches is O(N2) = too slow.",
    "",
    "Solution: divide feature map into 7x7 windows.",
    "  56x56 patches  /  7x7 window = 64 local windows",
    "  Attention runs WITHIN each window (49 tokens each)",
    "  Cost: 64 x O(492)  instead of O(3,1362)",
    "",
    "Inside each window — standard attention:",
    "  Q = token x W_Q   (what am I looking for?)",
    "  K = token x W_K   (what do I contain?)",
    "  V = token x W_V   (what info do I carry?)",
    "",
    "  Attention = softmax( QKT / sqrt(d) + B ) x V",
    "",
    "  B = Relative Position Bias (learned)",
    "  Encodes: 'these patches are 3 apart horizontally'",
    "  Teaches model: nearby lesions are more related.",
], 0.5, 1.92, 5.7, 4.75, size=12, color=WHITE)

# Right: SW-MSA innovation
box(sl, 6.6, 1.3, 6.4, 5.5, CARD_BG)
box(sl, 6.6, 1.3, 0.06, 5.5, YELLOW)
txt(sl, "Shifted Window MSA (SW-MSA) — Key Innovation", 6.8, 1.38, 6.1, 0.48, size=15, bold=True, color=YELLOW)

txt_lines(sl, [
    "Problem with W-MSA: patches at window BOUNDARIES",
    "never communicate. Two adjacent windows are isolated.",
    "",
    "Solution: alternate layers shift windows by (3,3):",
    "",
    "  Layer 1 (W-MSA):   aligned windows A B C D",
    "  Layer 2 (SW-MSA):  shift by half-window (3,3)",
    "                     new window E crosses A/B/C/D",
    "",
    "Window E crosses the original boundaries",
    "=> information flows between previously isolated windows.",
    "",
    "After many such layer pairs:",
    "  A patch on one side of the leaf can influence",
    "  a patch on the opposite side.",
    "",
    "For plant disease: the model can detect that",
    "  'brown edge lesion' + 'yellowing near centre'",
    "  together = a spreading blight pattern.",
    "  A ResNet cannot make this connection.",
], 6.8, 1.92, 6.1, 4.75, size=12, color=WHITE)


# =============================================================
# SLIDE 5F — HOW SWIN PRODUCES THE 0.5 NECROSIS SCORE
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
slide_header(sl, "How Swin Produces the 0.5 Necrosis Score", "Tracing the complete path from pixel to concept score")
footer(sl)

# Full forward pass trace
box(sl, 0.3, 1.3, 7.8, 5.5, CARD_BG)
box(sl, 0.3, 1.3, 0.06, 5.5, ACCENT)
txt(sl, "Full Forward Pass — Grape Esca Image", 0.5, 1.38, 7.5, 0.48, size=16, bold=True, color=ACCENT)

steps_trace = [
    ("1", "Swin Stages 1-2", "Detects dark brown edges, rough lesion textures.\nThese features DO resemble necrotic tissue."),
    ("2", "Swin Stage 3-4",  "Understands spatial distribution — spots are\nscattered, not water-soaked margins.\nThis does NOT match bacterial necrosis."),
    ("3", "SE Block",        "Channel recalibration: amplifies disease-relevant\nchannels, suppresses irrelevant ones.\nOutput: 768-dim vector (mixed signals)."),
    ("4", "Necrosis Network","Linear(768->256): projects to necrosis-relevant space.\nBatchNorm + ReLU: normalise and keep positives.\nLinear(256->1): weighted vote -> scalar h3."),
    ("5", "Sigmoid(h3=0)",   "h3 = positive signals - negative signals = ~0\nSigmoid(0) = 0.50\nModel is mathematically uncertain — not random."),
]

y = 1.95
for num, stage, detail in steps_trace:
    box(sl, 0.4, y, 7.6, 0.95, RGBColor(0x1A, 0x35, 0x4E))
    txt(sl, num,   0.55, y+0.1, 0.35, 0.38, size=14, bold=True, color=ACCENT)
    txt(sl, stage, 1.0,  y+0.1, 2.2,  0.38, size=13, bold=True, color=YELLOW)
    txt(sl, detail, 3.3, y+0.06, 4.6, 0.8,  size=11, color=WHITE)
    y += 1.02

# Right: Why 0.5 is correct
box(sl, 8.4, 1.3, 4.7, 5.5, CARD_BG)
box(sl, 8.4, 1.3, 0.06, 5.5, YELLOW)
txt(sl, "Why 0.5 is CORRECT & Verifiable", 8.6, 1.38, 4.4, 0.48, size=15, bold=True, color=YELLOW)

txt_lines(sl, [
    "The sigmoid maps raw score h3 to [0,1]:",
    "",
    "  h3 = -4  =>  0.018 (definitely absent)",
    "  h3 = -2  =>  0.12  (absent)",
    "  h3 =  0  =>  0.50  (uncertain)",
    "  h3 = +2  =>  0.88  (present)",
    "  h3 = +4  =>  0.98  (definitely present)",
    "",
    "For Grape Esca:",
    "  Supporting necrosis:",
    "    dark tissue, dead-cell textures",
    "  Opposing necrosis:",
    "    no water-soaking, no bacterial",
    "    ooze margin, fungal not bacterial",
    "",
    "These cancel => h3 ~ 0 => 0.50",
    "",
    "Verification — Faithfulness Test:",
    "  Force necrosis=1 for all Grape Esca",
    "  => accuracy DROPS",
    "  => 0.5 was the correct operating point.",
    "",
    "0.5 = honest uncertainty, not failure.",
], 8.6, 1.9, 4.4, 4.75, size=11, color=WHITE)


# =============================================================
# SLIDE 6 — 12 CONCEPTS
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
slide_header(sl, "The 12 Biological Concepts", "The model thinks in terms of these symptoms — just like a plant doctor")
footer(sl)

concepts = [
    ("Lesion Color",    "Color changes on diseased tissue"),
    ("Lesion Shape",    "Geometric form of disease spots"),
    ("Lesion Spread",   "Extent of symptom progression"),
    ("Necrosis",        "Dead / dying tissue formation"),
    ("Chlorosis",       "Yellowing from chlorophyll loss"),
    ("Wilting",         "Drooping due to water stress"),
    ("Spotting",        "Discrete spot patterns on leaf"),
    ("Blight Pattern",  "Rapid necrotic spread pattern"),
    ("Mold Presence",   "Visible fungal growth on leaf"),
    ("Leaf Curl",       "Leaf deformation / curling"),
    ("Vein Discolor.",  "Color change along leaf veins"),
    ("Lesion Texture",  "Surface texture: rough or smooth"),
]

x_start, y_start = 0.3, 1.3
cols = 4
cw, ch = 3.0, 1.48
for i, (name, desc) in enumerate(concepts):
    col = i % cols
    row = i // cols
    cx = x_start + col * (cw + 0.18)
    cy = y_start + row * (ch + 0.08)
    box(sl, cx, cy, cw, ch, CARD_BG)
    box(sl, cx, cy, cw, 0.05, ACCENT)
    txt(sl, str(i+1), cx+0.12, cy+0.08, 0.4, 0.4, size=13, color=ACCENT, bold=True)
    txt(sl, name,     cx+0.45, cy+0.08, 2.4, 0.5, size=14, bold=True, color=WHITE)
    txt(sl, desc,     cx+0.12, cy+0.66, 2.7, 0.7, size=11, color=LIGHT_TXT)

txt(sl, "Each concept is a biologically meaningful symptom score (0 to 1) — the model must explain itself using these symptoms.",
    0.3, 6.85, 12.5, 0.35, size=13, color=LIGHT_TXT, align=PP_ALIGN.CENTER)


# =============================================================
# SLIDE 6B — 38 DISEASE CLASSES FULL BREAKDOWN
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
slide_header(sl, "38 Disease Classes — Full Breakdown", "14 crops · 37 disease types · healthy variant per crop")
footer(sl)

# Stat summary bar
card(sl, 0.3,  1.3, 2.9,  0.95, "Total Classes",    "38",          title_size=12, val_size=24)
card(sl, 3.45, 1.3, 2.9,  0.95, "Crop Species",     "14",          title_size=12, val_size=24)
card(sl, 6.6,  1.3, 2.9,  0.95, "Disease Types",    "37",          title_size=12, val_size=24)
card(sl, 9.75, 1.3, 3.28, 0.95, "Largest Category", "Tomato (10)", title_size=12, val_size=18)

# ── Column 1: Tomato (10 classes) ──────────────────────────
box(sl, 0.3, 2.45, 3.5, 4.55, CARD_BG)
box(sl, 0.3, 2.45, 3.5, 0.05, ACCENT)
txt(sl, "Tomato — 10 classes", 0.45, 2.52, 3.2, 0.42, size=13, bold=True, color=ACCENT)
bullet_box(sl, [
    "Bacterial Spot",         "Early Blight",
    "Late Blight",            "Leaf Mold",
    "Septoria Leaf Spot",     "Spider Mites (Two-spotted)",
    "Target Spot",            "Yellow Leaf Curl Virus",
    "Mosaic Virus",           "Healthy",
], 0.45, 2.98, 3.2, 3.9, size=12, dot_color=ACCENT)

# ── Column 2: Apple + Corn ─────────────────────────────────
box(sl, 4.05, 2.45, 3.5, 2.1, CARD_BG)
box(sl, 4.05, 2.45, 3.5, 0.05, ACCENT)
txt(sl, "Apple — 4 classes", 4.2, 2.52, 3.2, 0.42, size=13, bold=True, color=ACCENT)
bullet_box(sl, ["Apple Scab", "Black Rot", "Cedar Apple Rust", "Healthy"],
           4.2, 2.98, 3.2, 1.5, size=12)

box(sl, 4.05, 4.7, 3.5, 2.3, CARD_BG)
box(sl, 4.05, 4.7, 3.5, 0.05, YELLOW)
txt(sl, "Corn — 4 classes", 4.2, 4.77, 3.2, 0.42, size=13, bold=True, color=YELLOW)
bullet_box(sl, ["Cercospora Leaf Spot", "Common Rust", "Northern Leaf Blight", "Healthy"],
           4.2, 5.22, 3.2, 1.65, size=12, dot_color=YELLOW)

# ── Column 3: Grape + Potato + Others ──────────────────────
PURPLE = RGBColor(0x8E, 0x44, 0xAD)
ORANGE_C = RGBColor(0xE6, 0x7E, 0x22)

box(sl, 7.8, 2.45, 5.2, 1.85, CARD_BG)
box(sl, 7.8, 2.45, 5.2, 0.05, PURPLE)
txt(sl, "Grape — 4 classes", 7.95, 2.52, 4.9, 0.42, size=13, bold=True, color=PURPLE)
bullet_box(sl, ["Black Rot", "Esca (Black Measles)", "Leaf Blight", "Healthy"],
           7.95, 2.98, 4.9, 1.25, size=12, dot_color=PURPLE)

box(sl, 7.8, 4.45, 2.45, 2.55, CARD_BG)
box(sl, 7.8, 4.45, 2.45, 0.05, ORANGE_C)
txt(sl, "Potato — 3 classes", 7.95, 4.52, 2.2, 0.42, size=12, bold=True, color=ORANGE_C)
bullet_box(sl, ["Early Blight", "Late Blight", "Healthy"],
           7.95, 4.98, 2.2, 1.9, size=12, dot_color=ORANGE_C)

box(sl, 10.45, 4.45, 2.55, 2.55, CARD_BG)
box(sl, 10.45, 4.45, 2.55, 0.05, LIGHT_TXT)
txt(sl, "Other 9 Crops", 10.6, 4.52, 2.3, 0.42, size=12, bold=True, color=LIGHT_TXT)
txt_lines(sl, [
    "Cherry: Powdery Mildew, Healthy",
    "Peach: Bacterial Spot, Healthy",
    "Pepper: Bacterial Spot, Healthy",
    "Strawberry: Leaf Scorch, Healthy",
    "Orange: Citrus Greening",
    "Blueberry / Raspberry / Soybean: Healthy",
    "Squash: Powdery Mildew",
], 10.6, 4.98, 2.3, 1.9, size=10, color=LIGHT_TXT)


# =============================================================
# SLIDE 7 — TRAINING RESULTS
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
slide_header(sl, "Results — Model Performance", "How accurate is the model?")
footer(sl)

card(sl, 0.3,  1.35, 2.9, 1.55, "Validation Accuracy",   "99.91%", val_size=26)
card(sl, 3.4,  1.35, 2.9, 1.55, "Validation F1 Score",   "99.78%", val_size=26)
card(sl, 6.5,  1.35, 2.9, 1.55, "Test Accuracy",         "99.25%", val_size=26)
card(sl, 9.6,  1.35, 2.9, 1.55, "Test F1 Score",         "98.27%", val_size=26)

add_img(sl, os.path.join(FIG, "fig3_training_history.png"),     0.3,  3.1,  width=6.3)
add_img(sl, os.path.join(FIG, "fig6_summary_metrics.png"),      6.8,  3.1,  width=6.2)


# =============================================================
# SLIDE 8 — CONFUSION MATRIX
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
slide_header(sl, "Confusion Matrix", "Visual check — did the model confuse any diseases?")
footer(sl)

txt(sl, "PlantVillage Validation Set (8,145 images)",
    0.3, 1.25, 6.2, 0.4, size=15, bold=True, color=ACCENT)
add_img(sl, os.path.join(FIG, "Validation_PlantVillage_confusion_matrix.png"),
        0.2, 1.65, width=6.4)

txt(sl, "Combined Test Set (8,311 images — includes real field photos)",
    6.85, 1.25, 6.2, 0.4, size=15, bold=True, color=YELLOW)
add_img(sl, os.path.join(FIG, "Test_Combined_confusion_matrix.png"),
        6.75, 1.65, width=6.4)

txt(sl, "Almost perfect diagonal — very few misclassifications across all 38 disease classes.",
    0.3, 7.0, 12.5, 0.35, size=14, color=LIGHT_TXT, align=PP_ALIGN.CENTER)


# =============================================================
# SLIDE 9 — XAI ANALYSIS
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
slide_header(sl, "Explainability (XAI) Analysis", "How do we know the model truly understands disease?")
footer(sl)

methods = [
    ("🔄  Counterfactual",   "Shows the minimum change to concepts\nneeded to flip a disease → healthy.\nTells farmers: 'fix THIS symptom first.'"),
    ("📈  Faithfulness AUC", "Insertion AUC: 0.847\nDeletion AUC: 0.312\nProves concepts genuinely drive decisions."),
    ("🎛  Intervention",     "Hard-setting each concept to 0 or 1\nand measuring accuracy change.\nShows which concepts matter most."),
    ("🏆  Importance Rank",  "Ranks concepts by mean activation\nacross all validation images.\nSurface the most common symptoms."),
]

x = 0.3
for title, desc in methods:
    box(sl, x, 1.35, 3.0, 4.0, CARD_BG)
    box(sl, x, 1.35, 3.0, 0.06, ACCENT)
    txt(sl, title, x+0.12, 1.45, 2.8, 0.55, size=15, bold=True, color=ACCENT)
    txt(sl, desc,  x+0.12, 2.05, 2.8, 3.1,  size=14, color=WHITE)
    x += 3.25

add_img(sl, os.path.join(XAI, "xai_fig2_faithfulness.png"), 0.3,  5.5, width=6.2)
add_img(sl, os.path.join(XAI, "xai_fig4_concept_importance.png"), 6.8, 5.5, width=6.2)


# =============================================================
# SLIDE 10 — DEPLOYMENT
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
slide_header(sl, "Deployment — Live Web Application", "Anyone can use it right now, from any browser")
footer(sl)

box(sl, 0.3, 1.3, 12.7, 1.0, CARD_BG)
txt(sl, "🌐  https://anushkamahraniya-palnt-disease-predictor.hf.space",
    0.5, 1.4, 12.3, 0.7, size=18, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)

features = [
    ("📤  Upload",      "Upload any leaf photo\nfrom phone or browser"),
    ("🔍  Predict",     "Get disease name +\nconfidence score instantly"),
    ("📊  XAI Chart",   "See which symptoms\nthe model detected"),
    ("⚡  Fast",        "INT8 quantised model:\n23% smaller, 1.3× faster"),
]

x = 0.3
for title, desc in features:
    box(sl, x, 2.5, 2.9, 2.0, CARD_BG)
    box(sl, x, 2.5, 2.9, 0.05, ACCENT)
    txt(sl, title, x+0.12, 2.6,  2.7, 0.5, size=16, bold=True, color=ACCENT)
    txt(sl, desc,  x+0.12, 3.15, 2.7, 1.2, size=15, color=WHITE)
    x += 3.26

add_img(sl, os.path.join(FIG, "app_demo.png"), 0.3, 4.65, width=12.7)
txt(sl, "Demo: Grape Esca (Black Measles) — 99.5% confidence | XAI shows lesion_spread & wilting activated",
    0.3, 7.05, 12.5, 0.35, size=13, color=LIGHT_TXT, align=PP_ALIGN.CENTER)


# =============================================================
# SLIDE 11 — COMPARISON WITH STATE OF THE ART
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
slide_header(sl, "Comparison with State-of-the-Art", "PlantDiseaseCBM vs other models")
footer(sl)

rows = [
    ("Model",                      "Accuracy",     "F1 Score",  "Explainability",    "Field Test", True),
    ("PlantDiseaseCBM (Ours)",     "99.91%",       "99.78%",    "✅ Concept (Full)", "✅ Yes",      False),
    ("Swin-Small (Black Box)",     "99.10%",       "99.01%",    "❌ None",           "❌ No",       False),
    ("ResNet-50 + GradCAM",        "98.20%",       "98.12%",    "⚠ Post-hoc only",  "❌ No",       False),
    ("Vision Transformer (ViT)",   "97.80%",       "97.70%",    "⚠ Attention map",  "❌ No",       False),
    ("VGG-16",                     "97.80%",       "97.75%",    "❌ None",           "❌ No",       False),
    ("MobileNet",                  "93.00%",       "92.30%",    "❌ None",           "✅ Yes",      False),
]

col_w = [3.8, 1.8, 1.8, 2.6, 1.8]
col_x = [0.3, 4.2, 6.1, 8.0, 10.7]
y = 1.3
for i, row in enumerate(rows):
    row_color = ACCENT2 if i == 1 else (RGBColor(0x1A, 0x30, 0x45) if i == 0 else CARD_BG)
    for j, (val, cw, cx) in enumerate(zip(row[:5], col_w, col_x)):
        box(sl, cx, y, cw-0.05, 0.62, row_color)
        fc = WHITE if (i == 0 or i == 1) else LIGHT_TXT
        bold = (i <= 1)
        txt(sl, val, cx+0.08, y+0.1, cw-0.15, 0.45, size=13, color=fc, bold=bold)
    y += 0.68

txt(sl, "PlantDiseaseCBM is the ONLY model that is accurate AND explainable AND tested on real field images.",
    0.3, 6.95, 12.5, 0.4, size=14, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)


# =============================================================
# SLIDE 12 — PUBLICATION
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
slide_header(sl, "Publication", "Research accepted at an international conference")
footer(sl)

box(sl, 0.3, 1.3, 12.7, 5.4, CARD_BG)
box(sl, 0.3, 1.3, 0.08, 5.4, ACCENT)

pub = [
    ("Paper Title",  "Counterfactual Concept Bottleneck Networks with Squeeze-and-Excitation\nfor Explainable Plant Disease Diagnosis"),
    ("Conference",   "ICDAM 2026 — 7th International Conference on Data Analytics & Management"),
    ("Paper ID",     "1082"),
    ("Track",        "SS-13: AI and ML for Secure, Explainable, and Sustainable Systems"),
    ("Publisher",    "Springer Nature – LNNS Series"),
    ("Indexed",      "SCOPUS, INSPEC, zbMATH, SCImago"),
    ("Status",       "✅ Accepted — Presentation scheduled"),
]

y = 1.4
for label, val in pub:
    txt(sl, label + ":", 0.55, y, 2.2, 0.52, size=14, bold=True, color=ACCENT)
    txt(sl, val,         2.8,  y, 10.0, 0.52, size=14, color=WHITE)
    y += 0.7

add_img(sl, os.path.join(APP, "publication_email.png"), 0.3,  1.35, width=6.1)
add_img(sl, os.path.join(APP, "publication_cmt.png"),   6.65, 1.35, width=6.3)


# =============================================================
# SLIDE 13 — CONCLUSION
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
slide_header(sl, "Conclusion & Future Work", "What was achieved and what comes next?")
footer(sl)

box(sl, 0.3, 1.3, 6.1, 5.4, CARD_BG)
txt(sl, "✅  What We Achieved", 0.5, 1.4, 5.8, 0.5, size=18, bold=True, color=ACCENT)
bullet_box(sl, [
    "99.91% accuracy on 38 disease classes",
    "First CBM applied to multi-class\n   plant disease detection",
    "4 XAI tools for biological explanations",
    "Deployed live on Hugging Face Space",
    "Published at ICDAM 2026 (Springer LNNS)",
    "23% smaller model via INT8 quantisation",
], 0.5, 1.95, 5.8, 4.5, size=15)

box(sl, 6.9, 1.3, 6.1, 5.4, CARD_BG)
txt(sl, "🔭  Future Work", 7.1, 1.4, 5.8, 0.5, size=18, bold=True, color=YELLOW)
bullet_box(sl, [
    "Expert-annotated concept labels\n   from certified plant pathologists",
    "Expand to 30+ disease concepts",
    "TensorRT deployment for\n   NVIDIA Jetson edge devices",
    "Uncertainty estimation to flag\n   low-confidence predictions",
    "Mobile app for direct farmer use",
], 7.1, 1.95, 5.8, 4.5, size=15, dot_color=YELLOW)


# =============================================================
# SLIDE 14 — THANK YOU
# =============================================================
sl = prs.slides.add_slide(BLANK)
bg(sl)
box(sl, 0, 0, 0.12, 7.5, ACCENT)
box(sl, 0, 3.55, 13.33, 0.08, ACCENT)

txt(sl, "Thank You", 0.5, 1.0, 12.5, 1.5,
    size=54, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
txt(sl, "Questions & Discussion",
    0.5, 2.5, 12.5, 0.7, size=22, color=ACCENT, align=PP_ALIGN.CENTER)

txt(sl, "Anushka Mahraniya  |  20221CSD0151",
    0.5, 3.85, 12.5, 0.55, size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
txt(sl, "Guide: Meena Kumari K S",
    0.5, 4.4,  12.5, 0.45, size=16, color=LIGHT_TXT, align=PP_ALIGN.CENTER)
txt(sl, "Presidency University, Bengaluru",
    0.5, 4.85, 12.5, 0.45, size=16, color=LIGHT_TXT, align=PP_ALIGN.CENTER)

txt(sl, "🌐  https://anushkamahraniya-palnt-disease-predictor.hf.space",
    0.5, 5.5, 12.5, 0.5, size=16, bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
txt(sl, "📧  anushkamahraniya@gmail.com",
    0.5, 6.0, 12.5, 0.45, size=15, color=LIGHT_TXT, align=PP_ALIGN.CENTER)


# =============================================================
# SAVE
# =============================================================
out = os.path.join(BASE, "PlantDisease_Presentation_v2.pptx")
prs.save(out)
print(f"Presentation saved: {out}")
