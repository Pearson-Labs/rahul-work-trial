# 🚀 Vercel Deployment Guide

## 📋 **Prerequisites**

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI** (optional but recommended):
   ```bash
   npm install -g vercel
   ```

## 🛠️ **Deployment Steps**

### **1. Initialize Vercel Project**

From the backend directory:
```bash
cd /path/to/backend
vercel
```

Follow the prompts:
- **Set up project**: Yes
- **Project name**: `contract-analysis-backend` (or your preferred name)
- **Directory**: `.` (current directory)
- **Override settings**: No (use defaults)

### **2. Configure Environment Variables**

Add these environment variables in Vercel Dashboard or via CLI:

```bash
# AI & Analysis
vercel env add ANTHROPIC_API_KEY
vercel env add GEMINI_API_KEY

# Vector Database
vercel env add PINECONE_API_KEY
vercel env add PINECONE_INDEX_NAME
vercel env add PINECONE_ENVIRONMENT

# Database & Storage
vercel env add SUPABASE_URL
vercel env add SUPABASE_KEY

# Authentication
vercel env add CLERK_SECRET_KEY

# Google Drive Integration (JSON as string)
vercel env add GOOGLE_APPLICATION_CREDENTIALS_JSON
```

#### **Environment Variable Values:**

```bash
# Required API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key
GEMINI_API_KEY=your_gemini_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=contract-documents
PINECONE_ENVIRONMENT=us-east-1-aws
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
CLERK_SECRET_KEY=your_clerk_secret_key

# Google Credentials (paste entire JSON as string)
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"..."}
```

### **3. Deploy**

```bash
vercel --prod
```

Or push to connected Git repository for automatic deployment.

## 🔧 **Vercel Configuration**

The deployment uses these configuration files:

### **vercel.json**
```json
{
  "version": 2,
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "50mb"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ],
  "functions": {
    "main.py": {
      "maxDuration": 300
    }
  }
}
```

### **Serverless Handler**: `api/index.py`
Uses Mangum to adapt FastAPI for AWS Lambda/Vercel.

## 🌐 **CORS Configuration**

Update CORS origins in `main.py` for production:

```python
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://your-frontend-domain.vercel.app",  # Add your frontend domain
    "https://your-custom-domain.com"           # Add custom domains
]
```

## 📊 **Monitoring & Debugging**

### **View Logs**
```bash
vercel logs
```

### **Check Function Status**
Visit your Vercel dashboard to monitor:
- Function executions
- Error rates
- Response times
- Build logs

### **Test Endpoints**
After deployment, test these endpoints:

```bash
# Health check
curl https://your-deployment.vercel.app/

# API documentation
https://your-deployment.vercel.app/docs

# Test analysis (requires authentication)
curl -X POST https://your-deployment.vercel.app/api/process \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT" \
  -d '{"prompt": "Find termination clauses", "analysis_type": "general"}'
```

## ⚠️ **Important Considerations**

### **Serverless Limitations**
- **Cold starts**: First request may be slower
- **Timeout**: Max 300 seconds per request
- **Memory**: Limited to Vercel plan limits
- **File system**: Read-only except /tmp

### **Performance Optimization**
1. **Keep functions warm**: Regular health checks
2. **Optimize imports**: Use lazy loading where possible
3. **Cache results**: Implement caching for frequent queries
4. **Monitor usage**: Track function execution times

### **Security**
- All environment variables are encrypted
- Never commit secrets to Git
- Use Vercel's built-in security features
- Enable HTTPS-only (automatic on Vercel)

## 🔄 **Continuous Deployment**

### **GitHub Integration**
1. Connect your repository to Vercel
2. Every push to main branch triggers deployment
3. Pull requests get preview deployments

### **Environment-Specific Deployments**
- **Production**: `main` branch
- **Preview**: Feature branches
- **Development**: Local development

## 🐛 **Common Issues**

### **Import Errors**
```bash
# If modules aren't found, check:
1. requirements.txt has correct versions
2. PYTHONPATH is set correctly in vercel.json
3. All dependencies are installed
```

### **Timeout Errors**
```bash
# For long-running analyses:
1. Increase maxDuration in vercel.json (max 300s)
2. Implement async processing with callbacks
3. Break large requests into smaller chunks
```

### **Cold Start Issues**
```bash
# To minimize cold starts:
1. Keep functions warm with scheduled pings
2. Optimize import statements
3. Use Vercel Pro for better performance
```

### **Environment Variables Not Loading**
```bash
# Check:
1. Variables are set in Vercel dashboard
2. Spelling matches exactly
3. Redeploy after adding new variables
```

## 📈 **Scaling Considerations**

### **Vercel Pro Features**
- Faster builds
- Better performance
- Advanced analytics
- Team collaboration

### **Database Optimization**
- Use connection pooling for Supabase
- Implement caching with Redis
- Optimize Pinecone index settings

### **Monitoring**
- Set up alerts for errors
- Monitor response times
- Track usage patterns

## 🎉 **Success!**

After deployment, your enhanced AI contract analysis platform will be available at:
- **API**: `https://your-deployment.vercel.app`
- **Documentation**: `https://your-deployment.vercel.app/docs`
- **Health Check**: `https://your-deployment.vercel.app/`

The platform now includes:
- ✅ LangGraph multi-agent orchestration
- ✅ Clickable citations with Google Drive links
- ✅ Confidence scoring and page tracking
- ✅ Smart retry logic with conditional edges
- ✅ Tool-based document analysis
- ✅ Serverless scalability on Vercel

---

*🚀 Your AI contract analysis platform is now live and ready to process legal documents at scale!*