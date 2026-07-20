import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import pandas as pd
import joblib
from tensorflow.keras.models import load_model

app = FastAPI(title="SoftInt Mini-SOAR ML API")

MODEL_PATH = "mlp_model.h5"
SCALER_PATH = "scaler.pkl"
ENCODERS_PATH = "label_encoders.pkl"
FEATURES_PATH = "features.pkl"

model = None
scaler = None
label_encoders = None
features_list = None

class TrafficRow(BaseModel):
    data: dict

@app.on_event("startup")
def load_assets():
    global model, scaler, label_encoders, features_list
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH) and os.path.exists(ENCODERS_PATH):
        model = load_model(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        label_encoders = joblib.load(ENCODERS_PATH)
        features_list = joblib.load(FEATURES_PATH)
        print("Modelo MLP y assets cargados correctamente.")
    else:
        print("ADVERTENCIA: Modelo o assets no encontrados. Ejecuta train.py.")

@app.post("/score")
def score_traffic(row: TrafficRow):
    if model is None:
        raise HTTPException(status_code=503, detail="Modelo no cargado.")
    
    try:
        # ponytail: dynamic feature extraction
        input_dict = {}
        for f in features_list:
            val = row.data.get(f)
            
            # Si es categórica, usar el LabelEncoder
            if f in label_encoders:
                le = label_encoders[f]
                val_str = str(val)
                # Hack simple para valores no vistos: asignar -1
                if val_str in le.classes_:
                    input_dict[f] = le.transform([val_str])[0]
                else:
                    input_dict[f] = -1
            else:
                # Numérica
                input_dict[f] = float(val) if val is not None else 0.0
                
        X = pd.DataFrame([input_dict], columns=features_list)
        
        # Escalar
        X_scaled = scaler.transform(X)
        
        # Predecir Probabilidad
        prob = float(model.predict(X_scaled, verbose=0)[0][0])
        
        # Clasificar
        prediction = "anomaly" if prob > 0.5 else "normal"
        
        return {
            "prediction": prediction,
            "probability": prob
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
