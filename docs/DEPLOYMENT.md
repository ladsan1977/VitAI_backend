# VitAI Backend - Deployment Guide

This guide covers deploying the VitAI Backend API to Render's free tier.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [Option A: Deploy via Render Dashboard](#option-a-deploy-via-render-dashboard)
- [Option B: Deploy via render.yaml](#option-b-deploy-via-renderyaml)
- [Environment Variables](#environment-variables)
- [Post-Deployment](#post-deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)
- [Upgrading to Paid Plan](#upgrading-to-paid-plan)

---

## Prerequisites

1. **Render Account** - Sign up at [render.com](https://render.com) (free, use GitHub login)
2. **GitHub Repository** - Code must be in a GitHub repository
3. **OpenAI API Key** - Get from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
4. **VitAI API Key** - Generate using the command below

### Generate VitAI API Key

```bash
python -c "import secrets; print(f'vitai_sk_prod_{secrets.token_urlsafe(32)}')"
```

Save this key securely - you'll need it for configuration.

---

## Deployment Options

### Option A: Deploy via Render Dashboard (Easiest)

**Best for:** First-time deployment, quick setup

1. **Go to Render Dashboard**
   - Visit [dashboard.render.com](https://dashboard.render.com)
   - Click **New** → **Web Service**

2. **Connect GitHub Repository**
   - Select your GitHub repository: `ladsan1977/VitAI_backend`
   - Click **Connect**

3. **Configure Service**
   - **Name:** `vitai-backend` (or your preferred name)
   - **Region:** `Oregon` (or choose closest to your users)
   - **Branch:** `main`
   - **Root Directory:** (leave blank)
   - **Runtime:** `Docker` (Render auto-detects Dockerfile)
   - **Instance Type:** **Free**

4. **Advanced Settings (Optional)**
   - Expand "Advanced" section
   - **Docker Command:** (leave blank - uses Dockerfile CMD)
   - **Health Check Path:** `/health`

5. **Click "Create Web Service"**
   - Render will start building immediately
   - Initial build takes 3-5 minutes

6. **Configure Environment Variables** (see [Environment Variables](#environment-variables) section below)

7. **Wait for Deployment**
   - Monitor in **Logs** tab
   - Service URL will be: `https://vitai-backend-<random>.onrender.com`

---

### Option B: Deploy via render.yaml (Infrastructure as Code)

**Best for:** Reproducible deployments, team workflows

1. **Verify render.yaml exists** in repository root
   ```bash
   cat render.yaml  # Should show service configuration
   ```

2. **Go to Render Dashboard**
   - Visit [dashboard.render.com](https://dashboard.render.com)
   - Click **New** → **Blueprint**

3. **Connect Repository**
   - Select your GitHub repository
   - Render will auto-detect `render.yaml`
   - Review the configuration

4. **Approve and Deploy**
   - Click **Apply**
   - Render creates service from YAML spec

5. **Configure Secret Environment Variables**
   - `OPEN_AI_KEY`, `API_KEY`, `CORS_ORIGINS` must be set manually
   - See [Environment Variables](#environment-variables) section

---

## Environment Variables

After service is created, configure environment variables:

### Navigate to Environment Settings

1. Go to your service in Render Dashboard
2. Click **Environment** tab (left sidebar)
3. Add the following variables:

### Required Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `OPEN_AI_KEY` | `sk-proj-...` | Your OpenAI API key |
| `API_KEY` | `vitai_sk_prod_...` | Generated VitAI API key |
| `CORS_ORIGINS` | `["https://your-frontend.com"]` | Frontend domain (JSON array) |

### Optional Variables (if not using render.yaml)

| Variable | Value | Description |
|----------|-------|-------------|
| `APP_ENV` | `production` | Application environment |
| `LOG_LEVEL` | `INFO` | Logging level |
| `HTTPS_ONLY` | `true` | Enforce HTTPS |
| `ALLOWED_HOSTS` | `["*.onrender.com"]` | Allowed hostnames |
| `RATE_LIMIT_PER_MINUTE` | `10` | Rate limit (requests/min) |
| `RATE_LIMIT_PER_HOUR` | `100` | Rate limit (requests/hour) |

### Setting Variables

**Via Dashboard:**
```
1. Click "Add Environment Variable"
2. Enter Key and Value
3. Click "Save Changes"
4. Service will auto-redeploy
```

**Example CORS Configuration:**
```
CORS_ORIGINS=["https://vitai-frontend.vercel.app","https://www.vitai.app"]
```

**Note:** Render auto-provides `PORT` variable - do not set it manually.

---

## Post-Deployment

### 1. Verify Deployment

**Check Service Status:**
- In Render Dashboard → Your Service
- **Status** should show "Live" (green)
- **Events** tab shows deployment history

**Test Health Endpoint:**
```bash
curl https://vitai-backend-<random>.onrender.com/health
```

Expected response:
```json
{"status":"ok","env":"production","version":"0.1.0"}
```

**Note:** First request may take 15-30 seconds (cold start on free tier)

### 2. Test API Endpoints

**AI Health Check:**
```bash
curl https://vitai-backend-<random>.onrender.com/api/v1/ai/health
```

**Test Authentication:**
```bash
curl -X POST "https://vitai-backend-<random>.onrender.com/api/v1/ai/analyze" \
  -H "X-API-Key: vitai_sk_prod_your_actual_key" \
  -F "images=@test-image.jpg" \
  -F "analysis_type=complete"
```

Expected: 200 OK with analysis results

**Test Invalid Key:**
```bash
curl -X POST "https://vitai-backend-<random>.onrender.com/api/v1/ai/analyze" \
  -H "X-API-Key: invalid_key" \
  -F "images=@test.jpg"
```

Expected: 403 Forbidden

### 3. Update Frontend CORS

Once frontend is deployed:

1. Go to Render Dashboard → Environment
2. Update `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=["https://your-actual-frontend.com"]
   ```
3. Save (triggers auto-redeploy)

### 4. Share API Details

Provide to frontend team:
- **API Base URL:** `https://vitai-backend-<random>.onrender.com`
- **API Key:** (via secure channel - password manager, encrypted message)
- **Rate Limits:** 10 requests/min, 100 requests/hour
- **Cold Starts:** First request after 15min sleep may take 15-30s
- **Endpoints:** See [API_USAGE.md](../docs/API_USAGE.md)

---

## Monitoring & Maintenance

### Free Tier Limitations

- **750 hours/month** free (enough for always-on)
- **Sleeps after 15 minutes** of inactivity
- **Cold start:** 15-30 seconds on first request after sleep
- **Shared resources:** CPU/RAM shared with other services
- **Community support** only

### Monitoring Dashboard

Access at: Render Dashboard → Your Service

**Logs Tab:**
- Real-time application logs
- Filter by date/time
- Search functionality

**Metrics Tab:**
- CPU usage
- Memory usage
- Request count
- Response times

**Events Tab:**
- Deployment history
- Configuration changes
- Auto-deploy triggers

### Cost Monitoring

**Render:**
- Check usage: Dashboard → Account → Usage
- Free tier: $0/month
- Monitor to ensure within 750 hours/month

**OpenAI:**
- Monitor at: [platform.openai.com/usage](https://platform.openai.com/usage)
- **Set hard limit:** Organization → Settings → Billing → Usage limits
- **Recommended limit:** $10/month for MVP

**Total Expected Cost:** $0-10/month (Render free + OpenAI usage)

### Keep Service Warm (Optional)

To avoid cold starts, use **UptimeRobot** (free tier):

1. Sign up at [uptimerobot.com](https://uptimerobot.com)
2. Add new monitor:
   - **Type:** HTTP(s)
   - **URL:** `https://vitai-backend-<random>.onrender.com/health`
   - **Interval:** 5 minutes
   - **Alert:** Email on downtime
3. This pings every 5 minutes, preventing sleep

**Trade-off:** Uses more of your 750 free hours, but eliminates cold starts

### Logs and Debugging

**View Real-Time Logs:**
```bash
# Install Render CLI (optional)
brew install render  # macOS
# or
npm install -g @render/cli

# View logs
render logs vitai-backend
```

**Common Log Locations:**
- **Application logs:** Render Dashboard → Logs
- **Build logs:** During deployment in Logs tab
- **Error logs:** Filter logs for "ERROR" or "WARNING"

---

## Troubleshooting

### Build Failures

**Symptom:** Deployment fails during build

**Solutions:**
1. Check **Logs** tab for error messages
2. Verify `Dockerfile` is valid:
   ```bash
   docker build -t vitai-test .
   ```
3. Ensure all dependencies in `pyproject.toml`
4. Check UV version compatibility

### Health Check Failures

**Symptom:** Service shows "Unhealthy"

**Solutions:**
1. Verify `/health` endpoint works locally:
   ```bash
   curl http://localhost:8000/health
   ```
2. Check `healthCheckPath: /health` in render.yaml
3. Ensure app binds to `0.0.0.0:$PORT`
4. Review logs for startup errors

### Environment Variable Issues

**Symptom:** 500 errors, missing config

**Solutions:**
1. Verify all required vars are set:
   - `OPEN_AI_KEY`
   - `API_KEY`
   - `CORS_ORIGINS`
2. Check variable format (JSON for CORS_ORIGINS)
3. Redeploy after changing variables

### CORS Errors

**Symptom:** Frontend gets CORS errors

**Solutions:**
1. Check `CORS_ORIGINS` includes frontend domain:
   ```
   CORS_ORIGINS=["https://your-frontend.com"]
   ```
2. Ensure HTTPS (not HTTP) in origins
3. No trailing slashes in URLs
4. Redeploy after updating CORS_ORIGINS

### Cold Starts

**Symptom:** First request slow (15-30s)

**Expected behavior** on free tier

**Solutions:**
1. Use UptimeRobot to keep warm (see above)
2. Upgrade to paid plan ($7/month) for always-on
3. Inform users of potential delay

### Rate Limiting

**Symptom:** 429 Too Many Requests

**Expected behavior** - rate limiting is working

**Solutions:**
1. Check rate limits in environment:
   - `RATE_LIMIT_PER_MINUTE=10`
   - `RATE_LIMIT_PER_HOUR=100`
2. Adjust limits if needed
3. Implement exponential backoff in client

---

## Upgrading to Paid Plan

### When to Upgrade

Consider upgrading to Render Paid ($7/month) when:

- ✅ Cold starts affect user experience
- ✅ Need always-on service (no sleep)
- ✅ Exceeding 10,000 requests/month
- ✅ Want custom domain with better DNS
- ✅ Need faster response times
- ✅ Require email support

### Upgrade Process

1. Go to Render Dashboard → Your Service
2. Click **Instance Type**
3. Select **Starter** ($7/month)
4. Confirm upgrade
5. Service migrates automatically (no downtime)

### Paid Plan Benefits

- **Always-on** (no sleep/cold starts)
- **Dedicated resources** (not shared)
- **Faster performance**
- **Email support**
- **Custom domains** included
- **Automatic SSL** for custom domains

---

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com)
- [VitAI API Usage Guide](./API_USAGE.md)
- [VitAI Development Guide](./DEVELOPMENT.md)
- [Render Status Page](https://status.render.com)

---

## Summary: Deployment Checklist

### Pre-Deployment
- [ ] Generate VitAI API key
- [ ] Have OpenAI API key ready
- [ ] Know frontend domain (or use placeholder)
- [ ] Code pushed to GitHub main branch

### Deployment
- [ ] Create Render web service (Docker)
- [ ] Select free tier
- [ ] Configure environment variables
- [ ] Wait for first deploy (3-5 min)
- [ ] Test health endpoint
- [ ] Test API with valid key
- [ ] Test API with invalid key (should fail)

### Post-Deployment
- [ ] Update CORS with frontend domain
- [ ] Share API details with frontend team
- [ ] Set up OpenAI usage limits
- [ ] Monitor logs for errors
- [ ] (Optional) Set up UptimeRobot
- [ ] Bookmark Render dashboard

### Monitoring
- [ ] Weekly: Check Render usage
- [ ] Weekly: Check OpenAI costs
- [ ] Monitor error logs
- [ ] Track response times
- [ ] Review rate limit violations

---

**Need Help?**

- Check logs in Render Dashboard
- Review [troubleshooting](#troubleshooting) section
- Render Community: [community.render.com](https://community.render.com)
- GitHub Issues: [github.com/anthropics/claude-code/issues](https://github.com/anthropics/claude-code/issues)
