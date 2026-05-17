import os
import io
import torch
import numpy as np
from PIL import Image
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from src.model import PlantDiseaseCBM, NUM_CONCEPTS, CONCEPT_NAMES
from src.dataset import get_val_transforms

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLANTVILLAGE_DIR = os.path.join(BASE_DIR, "data", "plantvillage", "plantvillage dataset", "color")
CHECKPOINT = os.path.join(BASE_DIR, "outputs", "checkpoints", "best_model.pth")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="Plant Disease Pathologist API")

# Setup CORS just in case
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Hardcoded class names for production so we don't need the massive dataset
class_names = [
    "Apple Apple scab", "Apple Black rot", "Apple Cedar apple rust", "Apple healthy",
    "Blueberry healthy", "Cherry (including sour) Powdery mildew", "Cherry (including sour) healthy",
    "Corn (maize) Cercospora leaf spot", "Corn (maize) Common rust", "Corn (maize) Northern Leaf Blight",
    "Corn (maize) healthy", "Grape Black rot", "Grape Esca (Black Measles)",
    "Grape Leaf blight (Isariopsis Leaf Spot)", "Grape healthy", "Orange Haunglongbing (Citrus greening)",
    "Peach Bacterial spot", "Peach healthy", "Pepper, bell Bacterial spot", "Pepper, bell healthy",
    "Potato Early blight", "Potato Late blight", "Potato healthy", "Raspberry healthy",
    "Soybean healthy", "Squash Powdery mildew", "Strawberry Leaf scorch", "Strawberry healthy",
    "Tomato Bacterial spot", "Tomato Early blight", "Tomato Late blight", "Tomato Leaf Mold",
    "Tomato Septoria leaf spot", "Tomato Spider mites Two-spotted spider mite", "Tomato Target Spot",
    "Tomato Yellow Leaf Curl Virus", "Tomato mosaic virus", "Tomato healthy"
]
short_names = [n[:40] for n in class_names]
num_classes = len(short_names)

# Load Model
print("Loading model...")
model = None
try:
    if os.path.exists(CHECKPOINT):
        ckpt = torch.load(CHECKPOINT, map_location=device)
        if "num_classes" in ckpt:
            num_classes = ckpt["num_classes"]
        model = PlantDiseaseCBM(num_classes=num_classes, num_concepts=NUM_CONCEPTS, pretrained=False).to(device)
        model.load_state_dict(ckpt["model"])
        model.eval()
        print("Model loaded successfully.")
    else:
        print(f"Warning: Checkpoint not found at {CHECKPOINT}. Ensure the model is trained.")
except Exception as e:
    print(f"Error loading model: {e}")

transform = get_val_transforms()

@app.post("/api/predict")
async def predict_disease(file: UploadFile = File(...)):
    if model is None:
        raise HTTPException(status_code=500, detail="Model is not loaded. Check checkpoint path.")
        
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        image_np = np.array(image)
        
        # apply transformations
        augmented = transform(image=image_np)
        img_tensor = augmented["image"].unsqueeze(0).to(device)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")
        
    with torch.no_grad():
        logits, concepts, _ = model(img_tensor)
        preds = logits.argmax(dim=1).item()
        probs = torch.nn.functional.softmax(logits, dim=1)[0]
        
    predicted_class = short_names[preds] if preds < len(short_names) else f"Class {preds}"
    confidence = probs[preds].item()
    
    # Concept Scores
    concept_scores = concepts[0].cpu().numpy().tolist()
    concept_dict = [{"name": CONCEPT_NAMES[i], "score": float(concept_scores[i])} for i in range(NUM_CONCEPTS)]
    
    return JSONResponse({
        "predicted_class": predicted_class,
        "confidence": confidence,
        "concepts": concept_dict
    })

# Mount the static directory for the frontend
# Ensure static dir exists before mounting
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    print("Starting FastAPI server on http://127.0.0.1:8000")
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
