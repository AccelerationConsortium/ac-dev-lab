#!/usr/bin/env python3
"""
Railway-ready FastAPI OT-2 Orchestration Server
Deploy with: railway up

This provides the same convenience as Prefect Cloud with built-in security.
"""

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
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration for Railway
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*.railway.app,localhost").split(",")

# Default users (use environment variables in production)
DEFAULT_USERS = {
    "ot2_user": os.getenv("OT2_PASSWORD", "demo_password_123"),
    "lab_admin": os.getenv("ADMIN_PASSWORD", "admin_password_456")
}

# Hash passwords on startup
USERS_DB = {}
for username, password in DEFAULT_USERS.items():
    USERS_DB[username] = {
        "password_hash": bcrypt.hashpw(password.encode(), bcrypt.gensalt()),
        "roles": ["admin"] if "admin" in username else ["operator"]
    }

app = FastAPI(
    title="OT-2 Cloud Orchestration Server",
    description="Railway-hosted OT-2 device orchestration with built-in security",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Security middleware
if ALLOWED_HOSTS != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Task registry - simple in-memory storage
tasks_registry = {}

def task(func):
    """Decorator to register OT-2 tasks for cloud execution."""
    import inspect
    
    # Get function signature for validation
    sig = inspect.signature(func)
    
    tasks_registry[func.__name__] = {
        'function': func,
        'signature': sig,
        'doc': func.__doc__ or "",
        'name': func.__name__
    }
    
    logger.info(f"Registered cloud task: {func.__name__}")
    return func

def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

def create_access_token(username: str, roles: list) -> str:
    """Create JWT access token."""
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode = {"sub": username, "roles": roles, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user info."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        roles = payload.get("roles", [])
        
        if username not in USERS_DB:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        return {"username": username, "roles": roles}
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

# ================== API ENDPOINTS ==================

@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "message": "🤖 OT-2 Cloud Orchestration Server",
        "status": "online",
        "hosting": "Railway.app",
        "security": "HTTPS + JWT",
        "tasks_available": list(tasks_registry.keys()),
        "endpoints": {
            "authentication": "/auth/login",
            "api_docs": "/docs",
            "task_list": "/tasks",
            "task_execution": "/execute/{task_name}"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/auth/login")
async def login(username: str, password: str):
    """Authenticate user and return JWT token."""
    user = USERS_DB.get(username)
    
    if not user or not verify_password(password, user["password_hash"]):
        logger.warning(f"Failed login attempt for username: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(username, user["roles"])
    
    logger.info(f"User '{username}' authenticated successfully")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600,
        "user": username,
        "roles": user["roles"]
    }

@app.get("/tasks")
async def list_tasks():
    """List all available OT-2 tasks."""
    tasks_info = {}
    
    for name, info in tasks_registry.items():
        # Get parameter info from signature
        params = {}
        for param_name, param in info['signature'].parameters.items():
            params[param_name] = {
                'type': str(param.annotation) if param.annotation != param.empty else 'Any',
                'default': param.default if param.default != param.empty else None,
                'required': param.default == param.empty
            }
        
        tasks_info[name] = {
            'name': name,
            'description': info['doc'],
            'parameters': params
        }
    
    return {
        "tasks": tasks_info,
        "count": len(tasks_registry),
        "server_info": {
            "hosting": "Railway.app",
            "security": "JWT Authentication Required"
        }
    }

@app.post("/execute/{task_name}")
async def execute_task(
    task_name: str,
    parameters: Dict[str, Any] = {},
    user_info: Dict[str, Any] = Depends(verify_token)
):
    """Execute a registered OT-2 task in the cloud."""
    if task_name not in tasks_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_name}' not found. Available: {list(tasks_registry.keys())}"
        )
    
    task_info = tasks_registry[task_name]
    func = task_info['function']
    
    try:
        # Validate parameters against function signature
        bound_args = task_info['signature'].bind(**parameters)
        bound_args.apply_defaults()
        
        # Execute the OT-2 task
        start_time = time.time()
        result = func(**bound_args.arguments)
        execution_time = time.time() - start_time
        
        # Log successful execution
        logger.info(
            f"User '{user_info['username']}' executed '{task_name}' "
            f"in {execution_time:.2f}s with parameters: {parameters}"
        )
        
        return {
            'task_name': task_name,
            'parameters': parameters,
            'result': result,
            'status': 'success',
            'execution_time_seconds': round(execution_time, 3),
            'executed_by': user_info['username'],
            'timestamp': datetime.utcnow().isoformat(),
            'server': 'railway.app'
        }
        
    except TypeError as e:
        logger.error(f"Parameter error for task '{task_name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid parameters for task '{task_name}': {str(e)}"
        )
    except Exception as e:
        logger.error(f"Execution error for task '{task_name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task execution failed: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "tasks_registered": len(tasks_registry),
        "server": "railway.app"
    }

# ================== OT-2 TASKS ==================

@task
def cloud_mix_colors(r: int, g: int, b: int, well: str = "A1") -> str:
    """
    Cloud-hosted color mixing simulation.
    
    Args:
        r: Red component (0-255)
        g: Green component (0-255) 
        b: Blue component (0-255)
        well: Target well (e.g., "A1")
        
    Returns:
        Mixing result message
    """
    # Simulate OT-2 operation (replace with real opentrons code)
    time.sleep(0.5)  # Simulate work
    
    # In real deployment, this would control actual OT-2:
    # protocol = opentrons.execute.get_protocol_api("2.16")
    # pipette.aspirate(r, red_reservoir)
    # pipette.dispense(r, plate[well])
    # ... etc
    
    return f"☁️ Cloud: Mixed RGB({r},{g},{b}) in well {well} via Railway.app"

@task
def cloud_move_sensor(well: str, action: str = "to") -> str:
    """
    Cloud-hosted sensor movement simulation.
    
    Args:
        well: Target well
        action: "to" (move to well) or "back" (return home)
        
    Returns:
        Movement result message
    """
    time.sleep(0.3)  # Simulate movement
    
    if action == "to":
        return f"☁️ Cloud: Sensor positioned over well {well}"
    else:
        return f"☁️ Cloud: Sensor returned to home position"

@task  
def cloud_get_status() -> Dict[str, Any]:
    """
    Get cloud server and simulated OT-2 status.
    
    Returns:
        Status information dictionary
    """
    return {
        "ot2_status": "ready",
        "cloud_hosting": "Railway.app",
        "security": "HTTPS + JWT authentication",
        "tasks_available": list(tasks_registry.keys()),
        "server_time": datetime.utcnow().isoformat(),
        "simulated": True,  # Change to False when using real OT-2
        "endpoint": os.getenv("RAILWAY_STATIC_URL", "localhost:8000")
    }

@task
def cloud_run_experiment(experiment_name: str, wells: list, colors: list) -> Dict[str, Any]:
    """
    Run a complete color mixing experiment in the cloud.
    
    Args:
        experiment_name: Name of the experiment
        wells: List of well positions (e.g., ["A1", "A2", "A3"])
        colors: List of RGB tuples (e.g., [[255,0,0], [0,255,0], [0,0,255]])
        
    Returns:
        Experiment results
    """
    if len(wells) != len(colors):
        raise ValueError("Number of wells must match number of colors")
    
    start_time = datetime.utcnow()
    results = []
    
    for well, color in zip(wells, colors):
        r, g, b = color
        mix_result = cloud_mix_colors(r, g, b, well)
        move_result = cloud_move_sensor(well, "to")
        
        # Simulate measurement
        time.sleep(0.2)
        measurement = {"well": well, "rgb": color, "measured_value": sum(color) / 3}
        
        # Return sensor
        return_result = cloud_move_sensor(well, "back")
        
        results.append({
            "well": well,
            "color": color,
            "mix_result": mix_result,
            "measurement": measurement,
            "completed": True
        })
    
    end_time = datetime.utcnow()
    
    return {
        "experiment_name": experiment_name,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": (end_time - start_time).total_seconds(),
        "wells_processed": len(wells),
        "results": results,
        "status": "completed",
        "cloud_server": "Railway.app"
    }

# ================== STARTUP ==================

if __name__ == "__main__":
    import uvicorn
    
    # Railway provides PORT environment variable
    port = int(os.getenv("PORT", 8000))
    
    print("=" * 60)
    print("🚀 OT-2 Cloud Orchestration Server Starting...")
    print("=" * 60)
    print(f"🌐 Hosting: Railway.app")
    print(f"🔒 Security: HTTPS + JWT Authentication")
    print(f"📋 Tasks: {len(tasks_registry)} registered")
    print(f"🔑 Default users: {list(USERS_DB.keys())}")
    print(f"📚 API Docs: /docs")
    print("=" * 60)
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )