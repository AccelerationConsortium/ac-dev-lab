# Railway Deployment for OT-2 Orchestration

This directory contains everything needed to deploy your OT-2 orchestration server to Railway - the easiest cloud deployment option equivalent to Prefect Cloud.

## 🚀 Quick Deploy (5 minutes)

### 1. Install Railway CLI
```bash
npm install -g @railway/cli
# or
curl -fsSL https://railway.app/install.sh | sh
```

### 2. Login and Initialize
```bash
railway login
railway init
```

### 3. Set Environment Variables (Important!)
```bash
# Set secure passwords (change these!)
railway variables set OT2_PASSWORD=your_secure_ot2_password_here
railway variables set ADMIN_PASSWORD=your_secure_admin_password_here

# Set JWT secret (this will be auto-generated)
railway variables set JWT_SECRET_KEY=$(openssl rand -base64 32)

# Optional: Set allowed hosts
railway variables set ALLOWED_HOSTS="*.railway.app,yourdomain.com"
```

### 4. Deploy
```bash
railway up
```

### 5. Get Your HTTPS URL
```bash
railway domain
```

**Result**: You'll get a secure HTTPS URL like `https://your-app.railway.app` with automatic SSL certificates!

## 🔗 Files Included

- **`main.py`** - Complete FastAPI server with JWT authentication
- **`requirements.txt`** - Python dependencies  
- **`Dockerfile`** - Railway deployment configuration
- **`railway_client_example.py`** - Example client code
- **`README.md`** - This deployment guide

## 🔒 Security Features (Built-in)

- ✅ **HTTPS encryption** - Automatic SSL certificates
- ✅ **JWT authentication** - Secure token-based auth
- ✅ **Password hashing** - bcrypt for secure passwords
- ✅ **CORS protection** - Configurable cross-origin policies
- ✅ **Input validation** - FastAPI automatic validation
- ✅ **Audit logging** - All requests logged

## 🧪 Testing Your Deployment

### Option 1: Web Interface
1. Visit `https://your-app.railway.app/docs`
2. Click "Authorize" and login with:
   - Username: `ot2_user`
   - Password: `your_secure_ot2_password_here`
3. Test the API endpoints interactively

### Option 2: Python Client
```python
# Update the URL in railway_client_example.py
RAILWAY_URL = "https://your-app.railway.app"

# Run the example
python railway_client_example.py
```

### Option 3: curl Commands
```bash
# Get auth token
curl -X POST "https://your-app.railway.app/auth/login" \
  -d "username=ot2_user&password=your_secure_ot2_password_here"

# Use token to execute task (replace YOUR_TOKEN)
curl -X POST "https://your-app.railway.app/execute/cloud_mix_colors" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"r": 255, "g": 128, "b": 64, "well": "A1"}'
```

## 🔄 Updating Your Deployment

```bash
# Make changes to your code
# Then redeploy
railway up
```

Railway automatically handles:
- Zero-downtime deployments  
- SSL certificate renewal
- Automatic scaling
- Health monitoring

## 💰 Railway Pricing

- **Free Tier**: $5 credit per month (enough for development/testing)
- **Hobby**: $20/month (production workloads)
- **Pro**: $99/month (team features)

Compare to:
- Prefect Cloud: $39+/month
- HiveMQ Cloud: $49+/month

## 🌟 Why Railway for OT-2 Orchestration?

### ✅ **Same Convenience as Prefect Cloud**
- One-command deployment (`railway up`)
- Automatic HTTPS with SSL certificates
- Built-in monitoring and logging
- Web interface for testing

### ✅ **Better for OT-2 Use Case**
- No pydantic version conflicts
- Works with existing Opentrons code
- Customizable authentication
- Direct HTTP API (no complex setup)

### ✅ **Production Ready**
- Auto-scaling based on demand
- 99.9% uptime SLA
- Global CDN and edge locations  
- Automatic backups and rollbacks

## 🔧 Customization

### Add Real OT-2 Integration
Replace the simulation code in `main.py`:

```python
@task
def real_mix_colors(r: int, g: int, b: int, well: str) -> str:
    """Real OT-2 color mixing."""
    import opentrons.execute
    
    protocol = opentrons.execute.get_protocol_api("2.16")
    # Your actual OT-2 code here...
    
    return f"Real OT-2: Mixed RGB({r},{g},{b}) in {well}"
```

### Add More Authentication Options
```python
# In main.py, add LDAP, OAuth, etc.
from fastapi_users import FastAPIUsers
# Configure your preferred auth provider
```

### Add Database Storage
```python
# Add PostgreSQL or MongoDB for task history
railway add postgresql
# Update main.py to use database
```

### Custom Domain
```bash
# Add your custom domain in Railway dashboard
# Railway handles SSL automatically
```

## 📞 Support

- **Railway Docs**: https://docs.railway.app/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Issues**: Open an issue in the ac-training-lab repository

This Railway deployment provides the same "click and deploy" experience as Prefect Cloud, with the same security guarantees, but fully compatible with your Opentrons package!