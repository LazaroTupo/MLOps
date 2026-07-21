import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import pandas as pd
import joblib

app = FastAPI(title="SoftInt Mini-SOAR ML API")

MODEL_TYPE = os.environ.get("MODEL_TYPE", "keras").lower()

model = None
scaler = None
label_encoders = None
features_list = None
classes_list = None

class TrafficRow(BaseModel):
    data: dict

@app.on_event("startup")
def load_assets():
    global model, scaler, label_encoders, features_list, classes_list
    
    print(f"Iniciando API con MODEL_TYPE = {MODEL_TYPE}")
    
    try:
        if MODEL_TYPE == "keras":
            from tensorflow.keras.models import load_model
            model = load_model("mlp_model.h5")
            scaler = joblib.load("scaler.pkl")
            label_encoders = joblib.load("label_encoders.pkl")
            features_list = joblib.load("features.pkl")
            print("Modelo Keras cargado correctamente.")
            
        elif MODEL_TYPE == "xgboost":
            import xgboost as xgb
            model = joblib.load("models/production/modelo_XGBClassifier.pkl")
            scaler = joblib.load("models/production/preprocessing.pkl")
            info = joblib.load("models/production/model_info.pkl")
            features_list = info.get("features", [])
            classes_list = info.get("classes", [])
            print("Modelo XGBoost cargado correctamente.")
            
        elif MODEL_TYPE == "pytorch":
            import torch
            import torch.nn as nn
            
            # Ingeniería inversa de la arquitectura original
            class CustomMLP(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.network = nn.Sequential(
                        nn.Linear(78, 128),
                        nn.ReLU(),
                        nn.Dropout(0.2), # Asumido, no afecta los pesos
                        nn.Linear(128, 64),
                        nn.ReLU(),
                        nn.Dropout(0.2),
                        nn.Linear(64, 11)
                    )
                def forward(self, x):
                    return self.network(x)
                    
            model = CustomMLP()
            state_dict = torch.load("models/experiments/modelo_MLP.pth", map_location=torch.device('cpu'))
            model.load_state_dict(state_dict)
            model.eval()
            
            scaler = joblib.load("models/experiments/preprocessing_MLP.pkl")
            info = joblib.load("models/experiments/model_info_MLP.pkl")
            features_list = info.get("input_features", [])
            classes_list = info.get("classes", [])
            print("Modelo PyTorch cargado correctamente mediante ingeniería inversa.")
            
        else:
            print(f"ADVERTENCIA: MODEL_TYPE '{MODEL_TYPE}' no es válido.")
    except Exception as e:
        print(f"ERROR AL CARGAR MODELO: {e}")

@app.post("/score")
def score_traffic(row: TrafficRow):
    if model is None:
        raise HTTPException(status_code=503, detail="Modelo no cargado.")
    
    try:
        # ponytail: dynamic feature extraction
        input_dict = {}
        for f in features_list:
            val = row.data.get(f)
            
            if MODEL_TYPE == "keras":
                if label_encoders and f in label_encoders:
                    le = label_encoders[f]
                    val_str = str(val)
                    if val_str in le.classes_:
                        input_dict[f] = le.transform([val_str])[0]
                    else:
                        input_dict[f] = -1
                else:
                    input_dict[f] = float(val) if val is not None else 0.0
            else:
                input_dict[f] = float(val) if val is not None else 0.0
                
        X = pd.DataFrame([input_dict], columns=features_list)
        
        if hasattr(scaler, 'transform'):
            X_scaled = scaler.transform(X)
        else:
            X_scaled = X.values
        
        prob = 0.0
        prediction = "normal"
        attack_category = "BENIGN"
        
        if MODEL_TYPE == "keras":
            prob = float(model.predict(X_scaled, verbose=0)[0][0])
            prediction = "anomaly" if prob > 0.5 else "normal"
            attack_category = "anomaly" if prob > 0.5 else "BENIGN"
            
        elif MODEL_TYPE == "xgboost":
            probs = model.predict_proba(X_scaled)[0]
            class_idx = int(np.argmax(probs))
            prob = float(probs[class_idx])
            attack_category = classes_list[class_idx]
            prediction = "normal" if attack_category == "BENIGN" else "anomaly"
            
        elif MODEL_TYPE == "pytorch":
            import torch
            with torch.no_grad():
                X_tensor = torch.FloatTensor(X_scaled)
                outputs = model(X_tensor)
                probs = torch.nn.functional.softmax(outputs, dim=1)[0]
                class_idx = int(torch.argmax(probs).item())
                prob = float(probs[class_idx])
                attack_category = classes_list[class_idx]
                prediction = "normal" if attack_category == "BENIGN" else "anomaly"
        
        return {
            "prediction": prediction,
            "probability": prob,
            "attack_category": attack_category
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
