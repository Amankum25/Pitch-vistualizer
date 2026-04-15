# 🚀 Pitch Visualizer Deployment Guide

This guide covers the deployment of the Pitch Visualizer system across the required infrastructure.

## 🏗️ Architecture Overview

| Component | Provider | Purpose |
|-----------|----------|---------|
| **Backend API** | [Render](https://render.com/) | FastAPI server running the LLM + GenAI pipeline |
| **Frontend UI** | [Vercel](https://vercel.com/) | Static hosting for the HTML/JS/CSS client |
| **Image Storage** | [Cloudinary](https://cloudinary.com/) | Permanent hosting for generated storyboard panels |
| **Keep-Alive** | [UptimeRobot](https://uptimerobot.com/) | 5-minute pings to prevent Render free-tier sleep |

---

## ☁️ 1. Cloudinary Setup (Storage)

The backend needs Cloudinary to store the MiniMax-generated images so the frontend can access them from anywhere.

1. Go to [Cloudinary](https://cloudinary.com/) and log in.
2. In the top left corner (next to the blue icon), copy your **Cloud Name** (e.g. `dpozbzted`). *Do NOT use the "Key Name" (like "PITCH Root") as the Cloud Name!*
3. Go to the **API Keys** section and copy your **API Key** and **API Secret**.
4. *(Optional)* Create a folder in your Cloudinary media library named `pitch-visualizer` (the backend code defaults to placing images here).

---

## ⚙️ 2. Render Deployment (Backend)

We will deploy the FastAPI backend as a Render **Web Service**.

### Prerequisites:
Make sure your `requirements.txt` includes exactly:
```text
fastapi>=0.111
uvicorn[standard]>=0.29
httpx>=0.27
groq>=0.9
python-dotenv>=1.0
pydantic>=2.6
Pillow>=10.3
cloudinary>=1.40
pytest>=8.0
pytest-asyncio>=0.23
```

### Steps:
1. Go to [Render Dashboard](https://dashboard.render.com/) → **New Web Service**.
2. Connect your GitHub repository (`Amankum25/Pitch-vistualizer`).
3. **Settings**:
   - **Language**: Python 3
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn src.app.main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables** (Add these in the Render dashboard):
   - `minimax_api`: (Your MiniMax API key)
   - `groq_api_key1`: (Your 1st Groq API key)
   - `groq_api_key2`: (Your 2nd Groq API key)
   - `groq_api_key3`: (Your 3rd Groq API key)
   - `groq_api_key4`: (Your 4th Groq API key)
   - `groq_api_key5`: (Your 5th Groq API key)
   - `CLOUDINARY_CLOUD_NAME`: (From step 1)
   - `CLOUDINARY_API_KEY`: (From step 1)
   - `CLOUDINARY_API_SECRET`: (From step 1)
   - `CORS_ORIGIN`: `*` (or your specific Vercel URL later for security)
   - `MOCK_IMAGES`: `false` (Make sure this is false in production)
5. Click **Create Web Service**. Wait for the build and copy the generated Render URL (e.g., `https://pitch-visualizer-api.onrender.com`).

---

## ⏰ 3. UptimeRobot Setup (Keep-Alive)

Render spins down free-tier services after 15 minutes of inactivity. To prevent cold boots (which ruin the required 20-30s latency constraint), we will ping it every 5 minutes.

1. Go to [UptimeRobot](https://uptimerobot.com/) and create a free account.
2. Click **Add New Monitor**.
3. **Settings**:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: Pitch Visualizer Backend
   - **URL (or IP)**: `<YOUR_RENDER_URL>/api/v1/health`
   - **Monitoring Interval**: 5 minutes
4. Click **Create Monitor**. The backend will now never spin down.

---

## 🌐 4. Vercel Deployment (Frontend)

Deploying the frontend as a static site.

### Modify API Base (Crucial Step):
Before pushing your final commit, point the frontend to your live Render backend.
Open `frontend/app.js` and change line 1:
```javascript
// Change this:
// const API_BASE = window.API_BASE || 'http://localhost:8000';

// To this:
const API_BASE = 'https://<YOUR_RENDER_URL>'; // Replace with actual render URL
```
*Commit and push this change to GitHub.*

### Steps:
1. Go to [Vercel](https://vercel.com/new).
2. Import your GitHub repository (`Amankum25/Pitch-vistualizer`).
3. **Settings**:
   - **Framework Preset**: Other
   - **Root Directory**: `frontend` (Important! Tell Vercel to only build the frontend folder).
4. Click **Deploy**. Vercel will instantly generate a live URL for your UI.

---

## ✅ Deployment Checklist

- [ ] Cloudinary keys retrieved and placed in Render.
- [ ] Render API is live and `/api/v1/health` returns `["status": "ok"]`.
- [ ] UptimeRobot is hitting the health endpoint every 5 minutes successfully.
- [ ] `.env` has `MOCK_IMAGES` set to `false` or removed entirely so real MiniMax images generate.
- [ ] `frontend/app.js` is updated with the Render API URL.
- [ ] Vercel UI is live and can successfully communicate with the Render API without CORS errors.
- [ ] `outputs/` logic works on Render (Render provides ephemeral storage for the HTML artifacts, which is sufficient since they are immediately returned as a `Download` or `View` link).
