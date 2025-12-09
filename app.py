from flask import Flask, request, jsonify
import requests
from PIL import Image, ImageDraw, ImageFont
from gtts import gTTS
import subprocess
import os
import tempfile
import random

app = Flask(__name__)

PEXELS_API_KEY = "1QxhdvjnytoRlGeKmMJHwYeBIBVvcFV5c9iuWrw0fqKlGMCNGq6r3q1d"

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "YouTube Video Generator API",
        "endpoints": ["/generate"]
    })

@app.route('/generate', methods=['POST'])
def generate_video():
    try:
        data = request.json
        quote = data.get('quote', 'No quote provided')
        author = data.get('author', 'Unknown')
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # 1. Fetch random background image from Pexels
        page = random.randint(1, 100)
        pexels_url = f"https://api.pexels.com/v1/search?query=nature+landscape&per_page=1&page={page}"
        headers = {"Authorization": PEXELS_API_KEY}
        
        response = requests.get(pexels_url, headers=headers)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch background image"}), 500
        
        photos = response.json().get('photos', [])
        if not photos:
            return jsonify({"error": "No images found"}), 500
        
        image_url = photos[0]['src']['large2x']
        
        # Download image
        img_response = requests.get(image_url)
        bg_path = os.path.join(temp_dir, 'background.jpg')
        with open(bg_path, 'wb') as f:
            f.write(img_response.content)
        
        # 2. Add text overlay
        img = Image.open(bg_path)
        img = img.resize((1920, 1080))  # HD resolution
        draw = ImageDraw.Draw(img)
        
        # Try to load font, fallback to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
            author_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 50)
        except:
            font = ImageFont.load_default()
            author_font = ImageFont.load_default()
        
        # Wrap text
        max_width = 1600
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
        line_height = 90
        total_height = len(lines) * line_height + 100
        y = (1080 - total_height) / 2
        
        # Draw text with shadow
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            x = (1920 - (bbox[2] - bbox[0])) / 2
            
            # Shadow
            draw.text((x+3, y+3), line, font=font, fill='black')
            # Main text
            draw.text((x, y), line, font=font, fill='white')
            y += line_height
        
        # Add author
        author_text = f"- {author}"
        bbox = draw.textbbox((0, 0), author_text, font=author_font)
        author_x = (1920 - (bbox[2] - bbox[0])) / 2
        draw.text((author_x+2, y+22), author_text, font=author_font, fill='black')
        draw.text((author_x, y+20), author_text, font=author_font, fill='white')
        
        # Save image
        quote_img_path = os.path.join(temp_dir, 'quote_image.jpg')
        img.save(quote_img_path, quality=95)
        
        # 3. Generate audio
        full_text = f"{quote}. By {author}"
        tts = gTTS(text=full_text, lang='en', slow=False)
        audio_path = os.path.join(temp_dir, 'audio.mp3')
        tts.save(audio_path)
        
        # 4. Create video with FFmpeg
        output_path = os.path.join(temp_dir, 'output.mp4')
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-loop', '1',
            '-i', quote_img_path,
            '-i', audio_path,
            '-c:v', 'libx264',
            '-tune', 'stillimage',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest',
            '-t', '15',  # Max 15 seconds
            output_path
        ]
        
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        
        # 5. Read video file and return as base64 or upload somewhere
        # For now, we'll return the file path (you'll need to handle file transfer)
        
        with open(output_path, 'rb') as f:
            video_data = f.read()
        
        # Clean up temp files
        import shutil
        shutil.rmtree(temp_dir)
        
        # Return video as binary in response
        from flask import send_file
        import io
        return send_file(
            io.BytesIO(video_data),
            mimetype='video/mp4',
            as_attachment=True,
            download_name=f'quote_video.mp4'
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
