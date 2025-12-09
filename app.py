from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
import subprocess
import os
import tempfile
import random
import shutil
import io
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PEXELS_API_KEY = os.environ.get('PEXELS_API_KEY', "1QxhdvjnytoRlGeKmMJHwYeBIBVvcFV5c9iuWrw0fqKlGMCNGq6r3q1d")

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "YouTube Video Generator API",
        "endpoints": ["/generate"]
    })

@app.route('/generate', methods=['POST'])
def generate_video():
    temp_dir = None
    try:
        logger.info("Starting video generation...")
        data = request.json
        quote = data.get('quote', 'No quote provided')
        author = data.get('author', 'Unknown')
        
        logger.info(f"Quote: {quote[:50]}... by {author}")
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Temp directory created: {temp_dir}")
        
        # 1. Fetch random background image from Pexels
        logger.info("Fetching background image from Pexels...")
        page = random.randint(1, 100)
        pexels_url = f"https://api.pexels.com/v1/search?query=nature+landscape&per_page=1&page={page}"
        headers = {"Authorization": PEXELS_API_KEY}
        
        response = requests.get(pexels_url, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.error(f"Pexels API error: {response.status_code}")
            return jsonify({"error": "Failed to fetch background image"}), 500
        
        photos = response.json().get('photos', [])
        if not photos:
            logger.error("No photos returned from Pexels")
            return jsonify({"error": "No images found"}), 500
        
        image_url = photos[0]['src']['large']  # Use 'large' instead of 'large2x' to save memory
        logger.info(f"Image URL: {image_url}")
        
        # Download image
        img_response = requests.get(image_url, timeout=15)
        bg_path = os.path.join(temp_dir, 'background.jpg')
        with open(bg_path, 'wb') as f:
            f.write(img_response.content)
        logger.info("Background image downloaded")
        
        # 2. Add text overlay
        logger.info("Processing image and adding text overlay...")
        img = Image.open(bg_path)
        img = img.resize((1280, 720))  # 720p instead of 1080p to reduce memory/processing
        draw = ImageDraw.Draw(img)
        
        # Try to load font, fallback to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
            author_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 35)
        except Exception as e:
            logger.warning(f"Font load failed: {e}, using default")
            font = ImageFont.load_default()
            author_font = ImageFont.load_default()
        
        # Wrap text
        max_width = 1100
        lines = []
        words = quote.split()
        current_line = ""
        
        for word in words:
            test_line = current_line + word + " "
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)
        
        # Calculate position
        line_height = 65
        total_height = len(lines) * line_height + 80
        y = (720 - total_height) / 2
        
        # Draw text with shadow
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            x = (1280 - (bbox[2] - bbox[0])) / 2
            
            # Shadow
            draw.text((x+2, y+2), line, font=font, fill='black')
            # Main text
            draw.text((x, y), line, font=font, fill='white')
            y += line_height
        
        # Add author
        author_text = f"- {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        author_x = (1280 - (bbox[2] - bbox[0])) / 2
        draw.text((author_x+2, y+17), author_text, font=author_font, fill='black')
        draw.text((author_x, y+15), author_text, font=author_font, fill='white')
        
        # Save image
        quote_img_path = os.path.join(temp_dir, 'quote_image.jpg')
        img.save(quote_img_path, quality=85)
        logger.info("Image saved with text overlay")
        
        # 3. Generate audio
        logger.info("Generating audio with gTTS...")
        full_text = f"{quote}. By {author}"
        tts = gTTS(text=full_text, lang='en', slow=False)
        audio_path = os.path.join(temp_dir, 'audio.mp3')
        tts.save(audio_path)
        logger.info("Audio generated")
        
        # 4. Create video with FFmpeg
        logger.info("Creating video with FFmpeg...")
        output_path = os.path.join(temp_dir, 'output.mp4')
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-loop', '1',
            '-i', quote_img_path,
            '-i', audio_path,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',  # Faster encoding
            '-tune', 'stillimage',
            '-c:a', 'aac',
            '-b:a', '128k',  # Lower audio bitrate
            '-pix_fmt', 'yuv420p',
            '-shortest',
            '-t', '15',  # Max 15 seconds
            '-loglevel', 'error',
            output_path
        ]
        
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=20)
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            return jsonify({"error": f"FFmpeg failed: {result.stderr}"}), 500
        
        logger.info("Video created successfully")
        
        # 5. Read video file and return
        logger.info("Reading video file...")
        if not os.path.exists(output_path):
            logger.error("Output video file not found")
            return jsonify({"error": "Video file not created"}), 500
        
        file_size = os.path.getsize(output_path)
        logger.info(f"Video file size: {file_size} bytes")
        
        with open(output_path, 'rb') as f:
            video_data = f.read()
        
        logger.info("Video generation completed successfully")
        
        # Return video as binary in response
        return send_file(
            io.BytesIO(video_data),
            mimetype='video/mp4',
            as_attachment=True,
            download_name=f'quote_video.mp4'
        )
        
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg timeout - video processing took too long")
        return jsonify({"error": "Video generation timeout"}), 504
    except Exception as e:
        logger.error(f"Error during video generation: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temp files
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info("Temp files cleaned up")
            except Exception as e:
                logger.warning(f"Failed to clean up temp dir: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

