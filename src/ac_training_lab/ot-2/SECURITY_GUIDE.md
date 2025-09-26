# Security Guide: FastAPI OT-2 Orchestration

This guide explains how to secure your FastAPI-based OT-2 orchestration for internet deployment with encryption, authentication, and privacy.

## 🔒 Security Overview

The FastAPI solution can be made as secure as Prefect and MQTT with proper configuration:

- **TLS Encryption** - HTTPS with SSL certificates
- **Authentication** - JWT tokens or API keys  
- **Authorization** - Role-based access control
- **Network Security** - VPN, firewalls, and port restrictions
- **Privacy** - No data logging, secure communication

## 🚀 Quick Security Setup

### 1. TLS/HTTPS Encryption

**Production deployment with reverse proxy (Recommended):**

```nginx
# /etc/nginx/sites-available/ot2-device
server {
    listen 443 ssl http2;
    server_name ot2-device.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/ot2-device.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ot2-device.yourdomain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Direct TLS with uvicorn:**

```python
# secure_device_server.py
import ssl
from ac_training_lab.ot_2.orchestration import DeviceServer

# Create SSL context
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain('/path/to/cert.pem', '/path/to/key.pem')

server = DeviceServer(require_auth=True)
server.run(
    host="0.0.0.0",
    port=8443,
    ssl_keyfile="/path/to/key.pem",
    ssl_certfile="/path/to/cert.pem"
)
```

### 2. Authentication & Authorization

**JWT Token Authentication:**

```python
# secure_server.py
import jwt
import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Generate a secure secret key
SECRET_KEY = secrets.token_urlsafe(32)  # Store this securely!
ALGORITHM = "HS256"

security = HTTPBearer()

def create_access_token(username: str, expires_delta: timedelta = timedelta(hours=1)):
    """Create a JWT token for authenticated access."""
    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": username, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return username."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Modify device server to require authentication
from ac_training_lab.ot_2.orchestration.device_server import DeviceServer

class SecureDeviceServer(DeviceServer):
    def _setup_routes(self):
        super()._setup_routes()
        
        # Override execute endpoint with authentication
        @self.app.post("/execute/{task_name}")
        async def secure_execute_task(
            task_name: str,
            parameters: Dict[str, Any] = {},
            username: str = Depends(verify_token)
        ):
            # Log the authenticated user
            logger.info(f"User '{username}' executing task '{task_name}'")
            
            # Call original execute logic
            return await super().execute_task(task_name, parameters)
        
        @self.app.post("/auth/login")
        async def login(username: str, password: str):
            # Implement your user verification logic
            if verify_user_credentials(username, password):
                token = create_access_token(username)
                return {"access_token": token, "token_type": "bearer"}
            else:
                raise HTTPException(status_code=401, detail="Invalid credentials")

def verify_user_credentials(username: str, password: str) -> bool:
    """Implement your user authentication logic."""
    # Example: check against database, LDAP, etc.
    # NEVER store passwords in plaintext!
    import bcrypt
    stored_hash = get_user_password_hash(username)  # From your database
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
```

**Client with Authentication:**

```python
# secure_client.py
from ac_training_lab.ot_2.orchestration import OrchestratorClient
import httpx

class SecureOrchestratorClient(OrchestratorClient):
    def __init__(self, base_url: str, username: str, password: str):
        super().__init__(base_url)
        self.token = self._authenticate(username, password)
        self.headers['Authorization'] = f'Bearer {self.token}'
    
    def _authenticate(self, username: str, password: str) -> str:
        """Authenticate and get JWT token."""
        response = httpx.post(
            f"{self.base_url}/auth/login",
            data={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()["access_token"]

# Usage
client = SecureOrchestratorClient(
    "https://ot2-device.yourdomain.com",
    username="lab_user",
    password="secure_password"
)
```

### 3. Network Security

**VPN Setup (OpenVPN example):**

```bash
# Install OpenVPN server
sudo apt update && sudo apt install openvpn easy-rsa

# Configure VPN server
sudo make-cadir /etc/openvpn/easy-rsa
cd /etc/openvpn/easy-rsa

# Generate certificates
./easyrsa init-pki
./easyrsa build-ca
./easyrsa gen-req server nopass
./easyrsa sign-req server server
./easyrsa gen-dh

# Configure OpenVPN
sudo cp pki/ca.crt pki/issued/server.crt pki/private/server.key pki/dh.pem /etc/openvpn/

# Create server config
sudo tee /etc/openvpn/server.conf << EOF
port 1194
proto udp
dev tun
ca ca.crt
cert server.crt
key server.key
dh dh.pem
server 10.8.0.0 255.255.255.0
push "redirect-gateway def1 bypass-dhcp"
push "dhcp-option DNS 8.8.8.8"
keepalive 10 120
cipher AES-256-CBC
user nobody
group nogroup
persist-key
persist-tun
status openvpn-status.log
verb 3
EOF

# Start OpenVPN
sudo systemctl enable openvpn@server
sudo systemctl start openvpn@server
```

**Firewall Configuration:**

```bash
# Configure iptables for security
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# Allow SSH (change port as needed)
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow VPN
sudo iptables -A INPUT -p udp --dport 1194 -j ACCEPT

# Allow HTTPS only (no HTTP)
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow OT-2 device server only from VPN network
sudo iptables -A INPUT -s 10.8.0.0/24 -p tcp --dport 8000 -j ACCEPT

# Allow loopback
sudo iptables -A INPUT -i lo -j ACCEPT

# Allow established connections
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Save rules
sudo iptables-save > /etc/iptables/rules.v4
```

## 🛡️ Complete Secure Deployment Example

```python
# secure_ot2_server.py
import os
import secrets
import bcrypt
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import jwt
from datetime import datetime, timedelta

from ac_training_lab.ot_2.orchestration import task, DeviceServer

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 1

# Allowed hosts (your domain)
ALLOWED_HOSTS = ["ot2-device.yourdomain.com", "localhost"]

# User database (use proper database in production)
USERS_DB = {
    "lab_admin": {
        "password_hash": bcrypt.hashpw(b"secure_admin_password", bcrypt.gensalt()),
        "roles": ["admin", "operator"]
    },
    "lab_operator": {
        "password_hash": bcrypt.hashpw(b"secure_operator_password", bcrypt.gensalt()),
        "roles": ["operator"]
    }
}

security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: bytes) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

def create_access_token(username: str, roles: list) -> str:
    """Create JWT access token."""
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode = {"sub": username, "roles": roles, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token and return user info."""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        roles = payload.get("roles", [])
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        return {"username": username, "roles": roles}
        
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

def require_role(required_role: str):
    """Decorator to require specific role."""
    def role_checker(user_info: Dict[str, Any] = Depends(verify_token)):
        if required_role not in user_info["roles"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return user_info
    return role_checker

# OT-2 Tasks (your actual tasks here)
@task()
def secure_mix_colors(r: int, g: int, b: int, well: str) -> str:
    """Secure color mixing task."""
    # Your OT-2 code here
    return f"Securely mixed RGB({r},{g},{b}) in well {well}"

@task() 
def secure_get_status() -> Dict[str, Any]:
    """Get secure status."""
    return {
        "status": "ready",
        "security": "enabled",
        "timestamp": datetime.utcnow().isoformat()
    }

# Create secure server
class SecureOT2Server(DeviceServer):
    def __init__(self):
        super().__init__(
            title="Secure OT-2 Device Server",
            description="Production-ready secure OT-2 orchestration server",
            require_auth=True
        )
        
        # Add security middleware
        self.app.add_middleware(
            TrustedHostMiddleware, 
            allowed_hosts=ALLOWED_HOSTS
        )
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://ot2-dashboard.yourdomain.com"],  # Your frontend
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )
        
        self._add_auth_routes()
        self._secure_existing_routes()
    
    def _add_auth_routes(self):
        """Add authentication routes."""
        
        @self.app.post("/auth/login")
        async def login(username: str, password: str):
            """Authenticate user and return JWT token."""
            user = USERS_DB.get(username)
            
            if not user or not verify_password(password, user["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password"
                )
            
            access_token = create_access_token(username, user["roles"])
            
            logging.info(f"User '{username}' authenticated successfully")
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_HOURS * 3600
            }
    
    def _secure_existing_routes(self):
        """Override existing routes with security."""
        
        # Secure task execution (operators can execute tasks)
        @self.app.post("/execute/{task_name}")
        async def secure_execute_task(
            task_name: str,
            parameters: Dict[str, Any] = {},
            user_info: Dict[str, Any] = Depends(require_role("operator"))
        ):
            logging.info(f"User '{user_info['username']}' executing task '{task_name}'")
            
            # Call parent class execute logic (but we need to reimplement it)
            if task_name not in _task_registry:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task '{task_name}' not found"
                )
            
            task_info = _task_registry[task_name]
            func = task_info['function']
            
            try:
                bound_args = task_info['signature'].bind(**parameters)
                bound_args.apply_defaults()
                
                result = func(**bound_args.arguments)
                
                return {
                    'task_name': task_name,
                    'parameters': parameters,
                    'result': result,
                    'status': 'success',
                    'executed_by': user_info['username']
                }
                
            except Exception as e:
                logging.error(f"Task execution failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

def main():
    """Run the secure server."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run server
    server = SecureOT2Server()
    
    print("🔒 Starting Secure OT-2 Device Server...")
    print("🌐 Use HTTPS in production!")
    print("🔑 JWT authentication enabled")
    print("🛡️  Role-based access control active")
    
    # In production, use proper SSL certificates
    server.run(
        host="0.0.0.0",
        port=8000,
        # ssl_keyfile="/path/to/private.key",
        # ssl_certfile="/path/to/certificate.crt"
    )

if __name__ == "__main__":
    main()
```

## 🔐 Client Security Example

```python
# secure_orchestrator.py
import os
import httpx
from ac_training_lab.ot_2.orchestration import OrchestratorClient

class SecureOrchestratorClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        self.client = httpx.Client(
            timeout=30.0,
            verify=True,  # Verify SSL certificates
            headers={'User-Agent': 'OT2-Orchestrator/1.0'}
        )
        
        # Authenticate on initialization
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate and get JWT token."""
        response = self.client.post(
            f"{self.base_url}/auth/login",
            data={"username": self.username, "password": self.password}
        )
        response.raise_for_status()
        
        auth_data = response.json()
        self.token = auth_data["access_token"]
        
        # Set authorization header
        self.client.headers['Authorization'] = f'Bearer {self.token}'
        
        print(f"✅ Authenticated as {self.username}")
    
    def execute_task(self, task_name: str, **kwargs):
        """Execute a task securely."""
        response = self.client.post(
            f"{self.base_url}/execute/{task_name}",
            json=kwargs
        )
        
        if response.status_code == 401:
            # Token might be expired, re-authenticate
            self._authenticate()
            response = self.client.post(
                f"{self.base_url}/execute/{task_name}",
                json=kwargs
            )
        
        response.raise_for_status()
        return response.json()["result"]
    
    def close(self):
        """Close the client connection."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Usage example
def run_secure_experiment():
    # Use environment variables for credentials (never hardcode!)
    username = os.getenv("OT2_USERNAME")
    password = os.getenv("OT2_PASSWORD")
    device_url = "https://ot2-device.yourdomain.com"
    
    with SecureOrchestratorClient(device_url, username, password) as client:
        # Execute tasks securely
        result = client.execute_task(
            "secure_mix_colors",
            r=255, g=128, b=64, well="A1"
        )
        print(f"Secure execution result: {result}")

if __name__ == "__main__":
    run_secure_experiment()
```

## 📋 Security Checklist

### ✅ **Network Security**
- [ ] Use HTTPS/TLS encryption in production
- [ ] Configure proper SSL certificates (Let's Encrypt recommended)
- [ ] Set up VPN for device access
- [ ] Configure firewall to restrict access
- [ ] Use non-default ports where appropriate
- [ ] Enable fail2ban for brute force protection

### ✅ **Authentication & Authorization**  
- [ ] Implement JWT token authentication
- [ ] Use strong password policies
- [ ] Enable role-based access control
- [ ] Set appropriate token expiration times
- [ ] Log all authentication attempts
- [ ] Implement account lockout after failed attempts

### ✅ **Data Protection**
- [ ] Never log sensitive parameters
- [ ] Use environment variables for secrets
- [ ] Encrypt sensitive data at rest
- [ ] Implement secure session management
- [ ] Regular security audits and updates

### ✅ **Monitoring & Logging**
- [ ] Log all API access attempts
- [ ] Monitor for suspicious activity
- [ ] Set up alerting for security events
- [ ] Regular log review and retention policies
- [ ] Intrusion detection system (IDS)

## 🆚 Security Comparison

| Feature | Prefect | FastAPI (Our Solution) | MQTT |
|---------|---------|----------------------|------|
| **Encryption** | ✅ HTTPS/TLS | ✅ HTTPS/TLS | ✅ TLS/SSL |
| **Authentication** | ✅ Built-in | ✅ JWT/Custom | ✅ Username/Password |
| **Authorization** | ✅ RBAC | ✅ Custom RBAC | 🔶 Basic |
| **Audit Logging** | ✅ Built-in | ✅ Custom | 🔶 Basic |
| **Enterprise SSO** | ✅ Yes | 🔶 Custom | ❌ Limited |
| **Network Security** | ✅ VPN/Proxy | ✅ VPN/Proxy | ✅ VPN/Broker |
| **Setup Complexity** | High | Medium | Low |

## 🌐 Internet Deployment Scenarios

### **Scenario 1: Corporate Network**
- Use corporate VPN infrastructure  
- HTTPS with corporate SSL certificates
- LDAP/Active Directory integration
- Corporate firewall and monitoring

### **Scenario 2: Cloud Deployment**
- AWS/Azure/GCP with load balancers
- Cloud-native SSL/TLS termination
- IAM integration for authentication
- Cloud security groups and WAF

### **Scenario 3: Hybrid Setup**
- On-premise OT-2 devices
- Cloud orchestration dashboard
- Site-to-site VPN connection
- Zero-trust network architecture

This comprehensive security setup ensures that your FastAPI-based OT-2 orchestration is as secure as Prefect and MQTT while maintaining compatibility with the Opentrons package.