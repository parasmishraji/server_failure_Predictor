import pandas as pd
import numpy as np
import xgboost as xgb
import os

# Set random seed for reproducibility
np.random.seed(42)

def generate_synthetic_data(num_samples=10000):
    """
    Generates synthetic server metric data.
    Features: cpu_usage, memory_usage, disk_io, network_latency
    Target: failure (0 or 1)
    """
    print(f"Generating {num_samples} samples of synthetic data...")
    
    # Healthy baseline
    cpu = np.random.normal(loc=40.0, scale=15.0, size=num_samples)
    memory = np.random.normal(loc=50.0, scale=20.0, size=num_samples)
    disk = np.random.exponential(scale=10.0, size=num_samples)
    network = np.random.lognormal(mean=2.0, sigma=0.5, size=num_samples)
    
    df = pd.DataFrame({
        'cpu_usage': np.clip(cpu, 0, 100),
        'memory_usage': np.clip(memory, 0, 100),
        'disk_io': disk,
        'network_latency': network
    })
    
    # Generate failures based on logic:
    # High CPU + High Memory OR Extremely High Disk OR High Latency
    failure_prob = (
        (df['cpu_usage'] > 85).astype(int) * 0.4 +
        (df['memory_usage'] > 90).astype(int) * 0.4 +
        (df['disk_io'] > 50).astype(int) * 0.3 +
        (df['network_latency'] > 50).astype(int) * 0.2
    )
    
    # Add random noise
    failure_prob += np.random.uniform(0, 0.2, size=num_samples)
    
    df['failure'] = (failure_prob > 0.8).astype(int)
    
    # Inject 25% missing data (NaNs) across features
    print("Injecting ~25% missing data (NaNs)...")
    for col in ['cpu_usage', 'memory_usage', 'disk_io', 'network_latency']:
        mask = np.random.rand(num_samples) < 0.25
        df.loc[mask, col] = np.nan
        
    return df

def train_and_save_model():
    df = generate_synthetic_data()
    
    X = df.drop(columns=['failure'])
    y = df['failure']
    
    print(f"Dataset shape: {X.shape}, Failures: {y.sum()} ({y.sum()/len(y)*100:.2f}%)")
    
    # XGBoost handles NaNs natively
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        objective='binary:logistic',
        missing=np.nan,
        random_state=42
    )
    
    print("Training XGBoost model...")
    model.fit(X, y)
    
    accuracy = model.score(X, y)
    print(f"Training Accuracy: {accuracy * 100:.2f}%")
    
    # Save the model
    model_path = os.path.join(os.path.dirname(__file__), 'xgboost_model.json')
    model.save_model(model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_and_save_model()
