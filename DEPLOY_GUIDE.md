# Deployment Guide - Render.com

## Step 1: Push Code to GitHub

1. Go to: https://github.com/new
2. Repository name: `youtube-video-generator`
3. Make it **Public**
4. Click **"Create repository"**
5. Follow the commands to push code:

```bash
cd c:\Users\prasa\OneDrive\Documents\MY_CODE\PROJ-0001\video-generator
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/youtube-video-generator.git
git push -u origin main
```

## Step 2: Deploy to Render.com

1. In Render.com, click **"New Web Service"**
2. Click **"Connect GitHub"** (if not already connected)
3. Select your repository: `youtube-video-generator`
4. Configure:
   - **Name**: `youtube-video-generator`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: **Free**
5. Click **"Advanced"**
6. Add Environment Variable:
   - Key: `PEXELS_API_KEY`
   - Value: `1QxhdvjnytoRlGeKmMJHwYeBIBVvcFV5c9iuWrw0fqKlGMCNGq6r3q1d`
7. Click **"Create Web Service"**

## Step 3: Wait for Deployment

Render will:
- Install dependencies
- Start the service
- Give you a URL like: `https://youtube-video-generator-xxxx.onrender.com`

## Step 4: Test the API

Once deployed, test it:

```bash
curl -X POST https://your-service-url.onrender.com/generate \
  -H "Content-Type: application/json" \
  -d '{"quote":"Success is not final, failure is not fatal","author":"Winston Churchill"}' \
  --output test.mp4
```

You should get a video file!

## Step 5: Update n8n Workflow

In n8n, add HTTP Request node:
- URL: `https://your-service-url.onrender.com/generate`
- Method: POST
- Body: `{"quote":"{{ $json.quote }}","author":"{{ $json.author }}"}`
- Response Format: **File**

Done!
