import pandas as pd
import numpy as np
import psycopg2
import os
import json
import kagglehub
from kagglehub import KaggleDatasetAdapter

def generate_synthetic_data():
    print("Descargando dataset NSL-KDD desde repositorio público...")
    
    # Nombres de las 43 columnas del dataset NSL-KDD
    col_names = [
        "duration","protocol_type","service","flag","src_bytes","dst_bytes","land",
        "wrong_fragment","urgent","hot","num_failed_logins","logged_in","num_compromised",
        "root_shell","su_attempted","num_root","num_file_creations","num_shells",
        "num_access_files","num_outbound_cmds","is_host_login","is_guest_login","count",
        "srv_count","serror_rate","srv_serror_rate","rerror_rate","srv_rerror_rate",
        "same_srv_rate","diff_srv_rate","srv_diff_host_rate","dst_host_count",
        "dst_host_srv_count","dst_host_same_srv_rate","dst_host_diff_srv_rate",
        "dst_host_same_src_port_rate","dst_host_srv_diff_host_rate","dst_host_serror_rate",
        "dst_host_srv_serror_rate","dst_host_rerror_rate","dst_host_srv_rerror_rate",
        "class", "difficulty_level"
    ]
    
    # ponytail: Usar URL directa evita problemas de autenticación de kagglehub (404 / 401).
    url = "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTrain%2B.csv"
    df = pd.read_csv(url, header=None, names=col_names)
    
    # Limpiamos: eliminamos difficulty_level (no es del paquete de red)
    df = df.drop(columns=["difficulty_level"])
    
    # Mapeamos 'normal' a 'normal' y cualquier otro ataque a 'anomaly'
    df['class'] = df['class'].apply(lambda x: 'normal' if x == 'normal' else 'anomaly')
    
    print(f"Dataset cargado con {len(df)} registros.")
    
    os.makedirs('../data', exist_ok=True)
    
    # El dataset de Kaggle trae 'class' (normal, anomaly).
    # Guardamos 80% para entrenar y 20% para test.
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    split_idx = int(len(df) * 0.8)
    
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    
    train_df.to_csv('../data/train_data.csv', index=False)
    test_df.to_csv('../data/test_data.csv', index=False)
    
    print(f"Datos generados: {len(train_df)} (Train), {len(test_df)} (Test)")
    return df

def setup_db(df):
    print("Insertando datos en PostgreSQL para el replayer...")
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        database="softint",
        user="admin",
        password="adminpassword",
        port=os.getenv("DB_PORT", "5432")
    )
    cur = conn.cursor()
    
    cur.execute("TRUNCATE TABLE incidents CASCADE;")
    cur.execute("TRUNCATE TABLE network_traffic CASCADE;")
    
    # Limitamos a 5000 para demostración en n8n
    df_sample = df.head(5000)
    
    insert_query = "INSERT INTO network_traffic (payload) VALUES (%s)"
    
    records = []
    for _, row in df_sample.iterrows():
        # Pasamos toda la fila a formato JSON para guardar en JSONB
        row_dict = row.to_dict()
        records.append((json.dumps(row_dict),))
        
    cur.executemany(insert_query, records)
    conn.commit()
    cur.close()
    conn.close()
    print(f"{len(df_sample)} registros insertados en PostgreSQL listos para n8n.")

if __name__ == "__main__":
    df = generate_synthetic_data()
    try:
        setup_db(df)
    except Exception as e:
        print(f"Error al conectar con Postgres: {e}")
        print("Asegúrate de ejecutar desde Docker o tener la BD levantada.")
