# Cloud Deployment Guide: FastAPI OT-2 Orchestration

This guide provides cloud hosting options for FastAPI-based OT-2 orchestration that offer the same convenience as Prefect Cloud and HiveMQ Cloud, with generous free tiers and built-in security.

## 🆚 Cloud Hosting Comparison

| Service | Free Tier | Security Built-in | OT-2 Suitable | Setup Complexity |
|---------|-----------|-------------------|----------------|------------------|
| **Railway** | ✅ $5 credit/month | ✅ HTTPS, Custom domains | ✅ Perfect | 🟢 Low |
| **Render** | ✅ 750h/month free | ✅ HTTPS, Auto SSL | ✅ Perfect | 🟢 Low |
| **Fly.io** | ✅ 3 small apps free | ✅ HTTPS, Global edge | ✅ Perfect | 🟡 Medium |
| **Heroku** | ❌ No free tier | ✅ HTTPS, Add-ons | ✅ Good | 🟢 Low |
| **Google Cloud Run** | ✅ 2M requests/month | ✅ HTTPS, IAM | ✅ Excellent | 🟡 Medium |
| **AWS Lambda + API Gateway** | ✅ 1M requests/month | ✅ HTTPS, IAM | 🟡 Limited | 🔴 High |

## 🚀 Recommended Solution: Railway (Easiest)

**Railway** is the closest equivalent to Prefect Cloud for FastAPI hosting - simple deployment with built-in security.

### Quick Railway Deployment

**1. Install Railway CLI:**
```bash
npm install -g @railway/cli
# or
curl -fsSL https://railway.app/install.sh | sh
```

**2. Create deployment files:**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Start the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```txt
# requirements.txt
fastapi==0.100.1
uvicorn[standard]==0.23.2
httpx==0.24.1
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
bcrypt==4.0.1
```

```python
# main.py
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os
import secrets
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

# Environment variables for Railway
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*.railway.app,*.yourdomain.com").split(",")

# Simple user store (use database in production)
USERS = {
    "ot2_user": bcrypt.hashpw(os.getenv("OT2_PASSWORD", "changeme123").encode(), bcrypt.gensalt()),
    "admin": bcrypt.hashpw(os.getenv("ADMIN_PASSWORD", "admin123").encode(), bcrypt.gensalt())
}

app = FastAPI(
    title="OT-2 Cloud Orchestration Server",
    description="Cloud-hosted OT-2 device orchestration with built-in security",
    version="1.0.0"
)

# Security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://*.yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Task registry
tasks_registry = {}

def task(func):
    """Simple task decorator for cloud deployment."""
    tasks_registry[func.__name__] = func
    return func

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if username not in USERS:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/auth/login")
async def login(username: str, password: str):
    """Authenticate and get token."""
    if username not in USERS or not bcrypt.checkpw(password.encode(), USERS[username]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = jwt.encode(
        {"sub": username, "exp": datetime.utcnow() + timedelta(hours=1)},
        SECRET_KEY,
        algorithm="HS256"
    )
    return {"access_token": token, "token_type": "bearer"}

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "message": "OT-2 Cloud Orchestration Server",
        "status": "online",
        "tasks": list(tasks_registry.keys()),
        "docs": "/docs",
        "auth": "/auth/login"
    }

@app.post("/execute/{task_name}")
async def execute_task(
    task_name: str,
    parameters: Dict[str, Any] = {},
    username: str = Depends(verify_token)
):
    """Execute a registered task."""
    if task_name not in tasks_registry:
        raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found")
    
    try:
        func = tasks_registry[task_name]
        result = func(**parameters)
        
        # Log execution
        logging.info(f"User '{username}' executed '{task_name}' with {parameters}")
        
        return {
            "task": task_name,
            "result": result,
            "status": "success",
            "executed_by": username
        }
    except Exception as e:
        logging.error(f"Task '{task_name}' failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Example OT-2 tasks
@task
def mix_colors(r: int, g: int, b: int, well: str = "A1") -> str:
    """Cloud-hosted color mixing task."""
    return f"Cloud: Mixed RGB({r},{g},{b}) in well {well}"

@task
def get_cloud_status() -> Dict[str, Any]:
    """Get cloud server status."""
    return {
        "status": "ready",
        "hosting": "railway",
        "security": "https+jwt",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

**3. Deploy to Railway:**
```bash
# Login to Railway
railway login

# Initialize project
railway init

# Set environment variables
railway variables set JWT_SECRET_KEY=$(openssl rand -base64 32)
railway variables set OT2_PASSWORD=your_secure_password
railway variables set ADMIN_PASSWORD=your_admin_password
railway variables set ALLOWED_HOSTS="*.railway.app,yourdomain.com"

# Deploy
railway up
```

**4. Get your secure HTTPS URL:**
```bash
railway domain  # Shows your *.railway.app URL with automatic HTTPS
```

### Client Usage with Railway:
```python
from httpx import Client

# Your Railway app URL (automatically has HTTPS)
DEVICE_URL = "https://your-app.railway.app"

def authenticate():
    """Get auth token from Railway-hosted server."""
    with Client() as client:
        response = client.post(
            f"{DEVICE_URL}/auth/login",
            data={"username": "ot2_user", "password": "your_secure_password"}
        )
        return response.json()["access_token"]

def execute_remote_task():
    """Execute task on Railway-hosted OT-2 server."""
    token = authenticate()
    
    with Client() as client:
        client.headers["Authorization"] = f"Bearer {token}"
        
        response = client.post(
            f"{DEVICE_URL}/execute/mix_colors",
            json={"r": 255, "g": 128, "b": 64, "well": "A1"}
        )
        
        return response.json()["result"]

# Usage
result = execute_remote_task()
print(f"Cloud execution result: {result}")
```

## 🌟 Alternative: Google Cloud Run (Most Robust)

For enterprise-grade deployment with Google's infrastructure:

### Cloud Run Deployment:

**1. Create `cloudbuild.yaml`:**
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/ot2-orchestrator', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/ot2-orchestrator']
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
    - 'run'
    - 'deploy'
    - 'ot2-orchestrator'
    - '--image'
    - 'gcr.io/$PROJECT_ID/ot2-orchestrator'
    - '--region'
    - 'us-central1'
    - '--allow-unauthenticated'
    - '--port'
    - '8000'
```

**2. Deploy:**
```bash
# Enable required APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com

# Deploy
gcloud builds submit --config cloudbuild.yaml

# Get URL
gcloud run services describe ot2-orchestrator --region=us-central1 --format="value(status.url)"
```

## 🔄 Migration from Existing Solutions

### From HiveMQ to Railway FastAPI:

**Before (HiveMQ MQTT):**
```python
# Device code
@mqtt_task
def mix_colors(r, g, b):
    return f"Mixed {r},{g},{b}"

server = MQTTDeviceServer("broker.hivemq.com", device_id="ot2-001")

# Client code  
with MQTTOrchestratorClient("broker.hivemq.com", "ot2-001") as client:
    result = client.execute_task("mix_colors", r=255, g=128, b=64)
```

**After (Railway FastAPI):**
```python
# Server code (deployed to Railway)
@task
def mix_colors(r, g, b):
    return f"Mixed {r},{g},{b}"

# Client code (anywhere on internet)
with SecureOrchestratorClient("https://your-app.railway.app") as client:
    result = client.execute_task("mix_colors", r=255, g=128, b=64)
```

## 🔒 Security Comparison

| Feature | Prefect Cloud | HiveMQ Cloud | Railway FastAPI | Google Cloud Run |
|---------|---------------|--------------|-----------------|------------------|
| **HTTPS/TLS** | ✅ Built-in | ✅ Built-in | ✅ Built-in | ✅ Built-in |
| **Authentication** | ✅ Built-in | ✅ Built-in | ✅ JWT (custom) | ✅ Google IAM |
| **Custom Domains** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **SSL Certificates** | ✅ Auto | ✅ Auto | ✅ Auto | ✅ Auto |
| **Firewall Rules** | ✅ Built-in | ✅ Built-in | ✅ Basic | ✅ Advanced |
| **DDoS Protection** | ✅ Yes | ✅ Yes | ✅ Basic | ✅ Google Shield |
| **Audit Logging** | ✅ Built-in | ✅ Built-in | 🔶 Custom | ✅ Cloud Logging |

## 💰 Cost Comparison (Monthly)

| Service | Free Tier | Paid Tier | Enterprise |
|---------|-----------|-----------|------------|
| **Prefect Cloud** | 20,000 task runs | $39+/month | Custom |
| **HiveMQ Cloud** | 100 connections | $49+/month | Custom |
| **Railway** | $5 credit | $20+/month | Custom |
| **Google Cloud Run** | 2M requests | Pay-per-use | Enterprise |
| **Render** | 750 hours | $7+/month | Custom |

## 📋 Quick Setup Checklist

### ✅ Railway Setup (5 minutes):
- [ ] Install Railway CLI
- [ ] Copy provided `main.py` and `Dockerfile`  
- [ ] Run `railway init && railway up`
- [ ] Set environment variables for passwords
- [ ] Test with provided client code
- [ ] **Result**: HTTPS endpoint ready with JWT auth

### ✅ Google Cloud Run (10 minutes):
- [ ] Enable Cloud Build and Cloud Run APIs
- [ ] Copy provided files and `cloudbuild.yaml`
- [ ] Run `gcloud builds submit`
- [ ] Configure custom domain (optional)
- [ ] Test with authentication
- [ ] **Result**: Enterprise-grade deployment

## 🔗 Integration with Existing Tools

Both Railway and Cloud Run integrate well with:
- **GitHub Actions** for CI/CD
- **Custom domains** with automatic SSL
- **Environment variables** for secrets management  
- **Monitoring and logging** built-in
- **Scaling** based on demand
- **Multiple regions** for global deployment

## 🎯 Recommendation

**For OT-2 Lab Use:**
- **Start with Railway** - Easiest setup, generous free tier, built-in security
- **Upgrade to Google Cloud Run** - When you need enterprise features
- **Both provide** the same convenience as Prefect Cloud + HiveMQ Cloud
- **Security equivalent** to enterprise solutions with HTTPS, authentication, and audit logging

This gives you the same "click and deploy" experience as Prefect Cloud, with the same security guarantees, but compatible with your Opentrons package.