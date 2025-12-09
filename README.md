# YouTube Video Generator API

Flask API service that generates motivational quote videos with:
- Background images from Pexels
- Text overlay with quote
- Text-to-speech audio
- Outputs MP4 video file

## Deploy to Render.com

1. Push this folder to GitHub
2. Connect GitHub repo to Render.com
3. Deploy as Web Service
4. Set environment variable: `PEXELS_API_KEY`

## API Endpoints

### POST /generate
Generate a video from quote text.

**Request:**
```json
{
  "quote": "The only way to do great work is to love what you do",
  "author": "Steve Jobs"
}
```

**Response:**
Returns MP4 video file as binary download.

## Local Testing

```bash
pip install -r requirements.txt
python app.py
```

Then test with:
```bash
curl -X POST http://localhost:10000/generate \
  -H "Content-Type: application/json" \
  -d '{"quote":"Test quote","author":"Test"}' \
  --output test.mp4
```
