import gradio as gr
import torch
import numpy as np
import os
import matplotlib.pyplot as plt

from model import PlantDiseaseCBM, NUM_CONCEPTS, CONCEPT_NAMES
from dataset import get_val_transforms

# Paths
# Adjust paths assuming script runs from the src directory or root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLANTVILLAGE_DIR = os.path.join(BASE_DIR, "data", "plantvillage", "plantvillage dataset", "color")
CHECKPOINT = os.path.join(BASE_DIR, "outputs", "checkpoints", "best_model.pth")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Fast class discovery
try:
    class_names = sorted([d for d in os.listdir(PLANTVILLAGE_DIR) if os.path.isdir(os.path.join(PLANTVILLAGE_DIR, d))])
    short_names = [n.replace("___", " ").replace("_", " ")[:40] for n in class_names]
    num_classes = len(class_names)
except Exception as e:
    # Fallback if path is wrong
    print(f"Warning: Could not load class names from {PLANTVILLAGE_DIR}. Error: {e}")
    short_names = [f"Class {i}" for i in range(38)]
    num_classes = 38

# Load Model
print("Loading model...")
try:
    ckpt = torch.load(CHECKPOINT, map_location=device)
    if "num_classes" in ckpt:
        num_classes = ckpt["num_classes"]
    model = PlantDiseaseCBM(num_classes=num_classes, num_concepts=NUM_CONCEPTS, pretrained=False).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

transform = get_val_transforms()

def predict(image):
    if model is None:
        return "Model not loaded. Please check checkpoint path.", {}, None
        
    if image is None:
        return "No image provided", {}, None

    # image is provided as numpy array by Gradio
    try:
        augmented = transform(image=image)
        img_tensor = augmented["image"].unsqueeze(0).to(device)
    except Exception as e:
        return f"Error processing image: {e}", {}, None
    
    with torch.no_grad():
        logits, concepts, _ = model(img_tensor)
        preds = logits.argmax(dim=1).item()
        probs = torch.nn.functional.softmax(logits, dim=1)[0]
        
    predicted_class = short_names[preds] if preds < len(short_names) else f"Class {preds}"
    confidence = probs[preds].item()
    
    # Concept Scores
    concept_scores = concepts[0].cpu().numpy()
    concept_dict = {CONCEPT_NAMES[i]: float(concept_scores[i]) for i in range(NUM_CONCEPTS)}
    
    # XAI Figure (Bar chart of concepts)
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = plt.cm.RdYlGn(concept_scores)
    bars = ax.bar(CONCEPT_NAMES, concept_scores, color=colors, edgecolor='black')
    ax.set_xticks(range(len(CONCEPT_NAMES)))
    ax.set_xticklabels(CONCEPT_NAMES, rotation=45, ha='right', fontsize=10)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Concept Activation Score (0=Absent, 1=Present)", fontsize=12)
    ax.set_title(f"Pathologist XAI: Concept Activations for '{predicted_class}'", fontsize=14, fontweight='bold')
    ax.axhline(0.5, color='gray', linestyle='--', alpha=0.7)
    
    # Add values on top of bars
    for bar, score in zip(bars, concept_scores):
        ax.text(bar.get_x() + bar.get_width()/2, score + 0.02, 
                f"{score:.2f}", ha='center', va='bottom', fontsize=9)
        
    plt.tight_layout()
    
    return f"{predicted_class} (Confidence: {confidence:.1%})", concept_dict, fig

# Custom CSS for better aesthetics
custom_css = """
.gradio-container {
    font-family: 'Inter', sans-serif;
}
.gr-button-primary {
    background: linear-gradient(90deg, #4CAF50 0%, #2E7D32 100%);
    border: none;
}
.gr-button-primary:hover {
    background: linear-gradient(90deg, #45a049 0%, #1b5e20 100%);
}
"""

with gr.Blocks() as interface:
    gr.Markdown(
        """
        # 🌿 Plant Disease Pathologist Dashboard
        Upload a photo of a plant leaf to predict the disease. 
        This dashboard uses a **Concept Bottleneck Model**, which not only predicts the disease but also provides interpretable symptom scores (concepts) such as *necrosis*, *chlorosis*, and *leaf curl*. This provides transparency and **Explainable AI (XAI)** for pathologists.
        """
    )
    
    with gr.Row():
        with gr.Column(scale=1):
            image_input = gr.Image(type="numpy", label="Upload Plant Image")
            predict_btn = gr.Button("Predict Disease & Analyze Symptoms", variant="primary")
            
        with gr.Column(scale=1):
            disease_output = gr.Textbox(label="Predicted Disease Diagnosis", text_align="center")
            concept_output = gr.Label(label="Symptom Concept Scores", num_top_classes=5)
            
    with gr.Row():
        xai_plot = gr.Plot(label="Pathologist XAI Dashboard - Complete Concept Profile")
        
    predict_btn.click(
        fn=predict,
        inputs=[image_input],
        outputs=[disease_output, concept_output, xai_plot]
    )
    
    gr.Markdown("---")
    gr.Markdown("*Developed with Gradio. The model is built on Swin Transformer with a Concept Bottleneck Head.*")

if __name__ == "__main__":
    print("Starting server on http://0.0.0.0:7865")
    interface.launch(server_name="0.0.0.0", server_port=7865, share=False)


