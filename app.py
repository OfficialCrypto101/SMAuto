import os
import logging
import uuid
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import re

from flask import Flask, request, jsonify, render_template, url_for
from apscheduler.schedulers.background import BackgroundScheduler

from utils.youtube import download_youtube_audio
from utils.audio import convert_to_assemblyai_format
from utils.cleanup import cleanup_old_files

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "youtube-audio-extractor-secret")

# Configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), "static", "audio")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
FILE_EXPIRATION_MINUTES = 60

# Initialize scheduler for cleanup tasks
scheduler = BackgroundScheduler()
scheduler.add_job(func=lambda: cleanup_old_files(UPLOAD_FOLDER, FILE_EXPIRATION_MINUTES), 
                 trigger="interval", 
                 minutes=15)
scheduler.start()

def is_valid_youtube_url(url):
    """Validate if the provided URL is a valid YouTube URL or video ID."""
    # Check if it's a valid URL
    try:
        parsed_url = urlparse(url)
        
        # If it's just a video ID (not a full URL)
        if not parsed_url.netloc:
            # Check if it matches YouTube video ID pattern (typically 11 chars)
            return bool(re.match(r'^[A-Za-z0-9_-]{11}$', url))
            
        # Check if it's a YouTube domain
        if parsed_url.netloc in ['youtube.com', 'www.youtube.com', 'youtu.be']:
            # For youtube.com, verify it has a video parameter
            if parsed_url.netloc in ['youtube.com', 'www.youtube.com']:
                query_params = parse_qs(parsed_url.query)
                return 'v' in query_params
            # For youtu.be, verify it has a path
            elif parsed_url.netloc == 'youtu.be':
                return bool(parsed_url.path and parsed_url.path != '/')
            
            return True
            
        return False
    except:
        return False

@app.route('/')
def index():
    """Render the homepage with a form to submit YouTube URLs."""
    return render_template('index.html')

@app.route('/download')
def download_audio():
    """
    API endpoint to download audio from a YouTube video.
    
    Query parameters:
    - url: YouTube video URL or video ID
    
    Returns:
    - JSON with audio URL or error message
    """
    youtube_url = request.args.get('url')
    
    if not youtube_url:
        return jsonify({'error': 'No URL provided'}), 400
    
    if not is_valid_youtube_url(youtube_url):
        return jsonify({'error': 'Invalid YouTube URL or video ID'}), 400
    
    try:
        # Generate a unique filename
        unique_id = str(uuid.uuid4())
        output_file_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}.mp3")
        
        # Download the YouTube audio
        logger.info(f"Downloading audio from: {youtube_url}")
        video_info = download_youtube_audio(youtube_url, output_file_path)
        
        if not video_info or not os.path.exists(output_file_path):
            return jsonify({'error': 'Failed to download audio from YouTube'}), 500
        
        # Verify the file size
        file_size = os.path.getsize(output_file_path)
        logger.info(f"Successfully downloaded audio: {output_file_path} (size: {file_size} bytes)")
        
        if file_size == 0:
            return jsonify({'error': 'Downloaded audio file is empty'}), 500
        
        # Create expiration timestamp (for information purposes)
        expiration_time = datetime.now() + timedelta(minutes=FILE_EXPIRATION_MINUTES)
        
        # Create a direct URL to the audio file
        audio_url = request.host_url.rstrip('/') + url_for('static', filename=f'audio/{unique_id}.mp3')
        
        # Store expiration timestamp in the file's metadata or a separate tracking system
        # For simplicity, we're just returning it in the response
        
        return jsonify({
            'success': True,
            'title': video_info.get('title', 'Unknown Title'),
            'audio_url': audio_url,
            'expiration': expiration_time.isoformat(),
            'expires_in_minutes': FILE_EXPIRATION_MINUTES
        })
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500

@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'error': 'Route not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500
