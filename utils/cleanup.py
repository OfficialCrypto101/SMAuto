import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def cleanup_old_files(directory, expiration_minutes):
    """
    Delete files in the specified directory that are older than the expiration time.
    
    Args:
        directory (str): Directory to clean up
        expiration_minutes (int): Number of minutes after which files should be deleted
    
    Returns:
        int: Number of files deleted
    """
    logger.info(f"Running cleanup of files older than {expiration_minutes} minutes in {directory}")
    
    if not os.path.exists(directory):
        logger.warning(f"Directory does not exist: {directory}")
        return 0
    
    # Calculate the cutoff time
    cutoff_time = datetime.now() - timedelta(minutes=expiration_minutes)
    count = 0
    
    try:
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            # Skip directories and non-audio files
            if os.path.isdir(file_path) or not (filename.endswith('.wav') or filename.endswith('.mp3')):
                continue
            
            # Get file's last modification time
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            # If the file is older than the cutoff time, delete it
            if file_mod_time < cutoff_time:
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted expired file: {filename}")
                    count += 1
                except Exception as e:
                    logger.error(f"Error deleting file {filename}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
    
    logger.info(f"Cleanup completed. Deleted {count} files.")
    return count
