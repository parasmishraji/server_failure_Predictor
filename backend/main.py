import asyncio
import json
import random
import os
import numpy as np
import pandas as pd
import xgboost as xgb
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the trained model
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'xgboost_model.json')
model = xgb.XGBClassifier()
if os.path.exists(MODEL_PATH):
    model.load_model(MODEL_PATH)
else:
    print("Warning: Model not found. Please run train_model.py first.")

# Simulate 20 servers across 4 Data Centers
DATA_CENTERS = ["US-East", "EU-West", "AP-South", "US-West"]
SERVERS = []
for i in range(20):
    SERVERS.append({
        "id": f"srv-{i+1:03d}",
        "dc": DATA_CENTERS[i % 4],
        "status": "Healthy"
    })

def generate_live_metrics():
    """Generates a single tick of live metrics for all servers"""
    data = []
    for srv in SERVERS:
        # Base healthy metrics
        cpu = np.clip(np.random.normal(40, 15), 0, 100)
        memory = np.clip(np.random.normal(50, 20), 0, 100)
        disk = np.random.exponential(10)
        network = np.random.lognormal(2.0, 0.5)
        
        # Introduce some failing servers arbitrarily (e.g. srv-003 and srv-012 might be struggling)
        if srv["id"] in ["srv-003", "srv-012"] and random.random() > 0.5:
            cpu = np.clip(np.random.normal(90, 5), 0, 100)
            memory = np.clip(np.random.normal(95, 5), 0, 100)
        
        # Inject ~10% missing data for live stream
        metrics = {
            "cpu_usage": cpu if random.random() > 0.1 else np.nan,
            "memory_usage": memory if random.random() > 0.1 else np.nan,
            "disk_io": disk if random.random() > 0.1 else np.nan,
            "network_latency": network if random.random() > 0.1 else np.nan
        }
        
        row = {
            "server_id": srv["id"],
            "data_center": srv["dc"],
            **metrics
        }
        data.append(row)
        
    return pd.DataFrame(data)

async def metric_streamer(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            if not os.path.exists(MODEL_PATH):
                await websocket.send_json({"error": "Model not trained yet."})
                await asyncio.sleep(2)
                continue
                
            # 1. Generate live data
            df = generate_live_metrics()
            
            # 2. Extract features for inference
            X_live = df[['cpu_usage', 'memory_usage', 'disk_io', 'network_latency']]
            
            # 3. Predict failure probabilities (< 5s latency constraint met easily)
            # XGBoost handles NaNs directly here
            probabilities = model.predict_proba(X_live)[:, 1]
            
            df['failure_probability'] = probabilities
            
            # 4. Determine status
            def get_status(prob):
                if prob > 0.8: return "Critical"
                if prob > 0.5: return "Warning"
                return "Healthy"
                
            df['status'] = df['failure_probability'].apply(get_status)
            
            # 5. Replace NaNs with None for JSON serialization
            df = df.replace({np.nan: None})
            
            payload = df.to_dict(orient='records')
            
            await websocket.send_json({"type": "metrics_update", "data": payload})
            
            # Stream every 2 seconds
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await metric_streamer(websocket)

@app.get("/")
def read_root():
    return {"message": "Server Failure Predictor Backend is running."}
