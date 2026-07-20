import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import f1_score, precision_score, recall_score, confusion_matrix
import joblib
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
import os

DATA_PATH = "../data/train_data.csv"
TEST_PATH = "../data/test_data.csv"

def train():
    if not os.path.exists(DATA_PATH):
        print("Error: train_data.csv no encontrado. Ejecuta setup_dataset.py.")
        return

    print("Cargando datos (Supervisado)...")
    df = pd.read_csv(DATA_PATH)
    
    # ponytail: The Kaggle dataset has categorical columns. We LabelEncode them to keep it simple.
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    if 'class' in categorical_cols:
        categorical_cols.remove('class')

    label_encoders = {}
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        label_encoders[col] = le
    
    # Guardamos los label encoders
    joblib.dump(label_encoders, 'label_encoders.pkl')

    # Convertimos la variable objetivo
    # 'normal' = 0, 'anomaly' = 1
    y_train = (df['class'] == 'anomaly').astype(int)
    X_train = df.drop(columns=['class'])
    
    features = X_train.columns.tolist()
    joblib.dump(features, 'features.pkl') # Para saber qué mandar en FastAPI

    print(f"Entrenando con {len(X_train)} muestras y {len(features)} variables.")

    # Escalar numéricos
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    joblib.dump(scaler, 'scaler.pkl')

    # --- MODELO RED NEURONAL SUPERVISADO (MLP) ---
    model = Sequential([
        Dense(32, activation='relu', input_shape=(len(features),)),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dense(1, activation='sigmoid')  # Devuelve PROBABILIDAD entre 0 y 1
    ])
    
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

    # Entrenar
    print("Iniciando entrenamiento MLP...")
    model.fit(
        X_train_scaled, y_train,
        epochs=10,
        batch_size=256,
        validation_split=0.1,
        verbose=1
    )

    model.save('mlp_model.h5')
    print("Modelo supervisado guardado con éxito.\n")
    
    # --- VALIDACIÓN ---
    if not os.path.exists(TEST_PATH):
        return
        
    print("--- EVALUACIÓN EN DATOS DE TEST ---")
    df_test = pd.read_csv(TEST_PATH)
    y_test = (df_test['class'] == 'anomaly').astype(int)
    X_test = df_test.drop(columns=['class'])
    
    # Transformar categoricas manejando valores desconocidos (ponytail hack: fallback a -1)
    for col in categorical_cols:
        le = label_encoders[col]
        # Si encuentra un valor nuevo, le asigna -1
        X_test[col] = X_test[col].map(lambda s: le.transform([s])[0] if s in le.classes_ else -1)
    
    # Rellenar NaNs por si hay nuevos features o errores
    X_test = X_test.fillna(0)
    
    X_test_scaled = scaler.transform(X_test)
    
    # Predicción (probabilidad)
    y_pred_prob = model.predict(X_test_scaled, verbose=0).flatten()
    
    # Usamos 0.5 como umbral clásico para clasificar
    y_pred = (y_pred_prob > 0.5).astype(int)
    
    print(f"Total datos test: {len(y_test)}")
    print(f" - Precisión (Precision): {precision_score(y_test, y_pred):.4f}")
    print(f" - Sensibilidad (Recall): {recall_score(y_test, y_pred):.4f}")
    print(f" - F1-Score:              {f1_score(y_test, y_pred):.4f}")
    
    cm = confusion_matrix(y_test, y_pred)
    print("\nMatriz de Confusión:")
    print(f"Verdaderos Normales (TN): {cm[0][0]} | Falsos Ataques (FP): {cm[0][1]}")
    print(f"Falsos Normales (FN):     {cm[1][0]} | Verdaderos Ataques (TP): {cm[1][1]}\n")

if __name__ == "__main__":
    train()
