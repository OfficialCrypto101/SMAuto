import os
import logging
import yt_dlp

logger = logging.getLogger(__name__)

def extract_video_id(url):
    """Extract the video ID from a YouTube URL if needed."""
    if "youtube.com" in url or "youtu.be" in url:
        return url  # Return the full URL since yt-dlp can handle it
    else:
        # Assume it's a video ID
        return f"https://www.youtube.com/watch?v={url}"

def download_youtube_audio(url, output_path):
    """
    Download audio from a YouTube video.
    
    Args:
        url (str): YouTube URL or video ID
        output_path (str): Path to save the downloaded audio
    
    Returns:
        dict: Video information or None if download failed
    """
    # Process the URL in case it's just a video ID
    processed_url = extract_video_id(url)
    
    # Remove .mp3 extension to prevent double extension
    base_path = output_path.replace('.mp3', '')
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': base_path,
        'noplaylist': True,
        'quiet': False,
        'no_warnings': False,
        'extractaudio': True,
        'audioformat': 'mp3',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    
    try:
        logger.info(f"Starting download from YouTube: {processed_url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(processed_url, download=True)
            
            # Check if file exists with potential .mp3 suffix added by yt-dlp
            expected_path = f"{base_path}.mp3"
            if os.path.exists(expected_path) and not os.path.exists(output_path):
                logger.info(f"Renaming output file to match expected path: {expected_path} -> {output_path}")
                os.rename(expected_path, output_path)
            
            # Verify file exists and has content
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                logger.info(f"Download complete. File size: {file_size} bytes")
                if file_size == 0:
                    logger.error("Downloaded file is empty")
                    os.remove(output_path)
                    return None
            else:
                logger.error(f"Output file not found at: {output_path}")
                return None
                
            # Return video information, useful for displaying title, etc.
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration'),
                'uploader': info.get('uploader', 'Unknown'),
                'thumbnail': info.get('thumbnail'),
            }
    except Exception as e:
        logger.error(f"Error downloading YouTube audio: {str(e)}")
        # Clean up any partially downloaded file
        if os.path.exists(output_path):
            os.remove(output_path)
        # Also check for the .mp3 extension variant
        mp3_path = f"{base_path}.mp3"
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
        return None
