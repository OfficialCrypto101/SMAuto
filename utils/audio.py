import os
import logging
import subprocess

logger = logging.getLogger(__name__)

def convert_to_assemblyai_format(input_path, output_path):
    """
    Convert audio to mono WAV at 16kHz (optimal for AssemblyAI).
    
    Args:
        input_path (str): Path to the input audio file
        output_path (str): Path to save the converted audio
    
    Returns:
        bool: True if conversion succeeded, False otherwise
    """
    try:
        # Verify the input file exists
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            return False
            
        # Check that the input file is not empty
        if os.path.getsize(input_path) == 0:
            logger.error(f"Input file is empty: {input_path}")
            return False
            
        logger.info(f"Input file exists and has size: {os.path.getsize(input_path)} bytes")
        
        # Use ffmpeg to convert to mono WAV at 16kHz
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ac', '1',               # Mono audio
            '-ar', '16000',           # 16kHz sample rate
            '-acodec', 'pcm_s16le',   # 16-bit PCM
            '-y',                     # Overwrite output file if it exists
            output_path
        ]
        
        logger.info(f"Running FFMPEG command: {' '.join(cmd)}")
        
        # Run the ffmpeg command with full output logging
        process = subprocess.run(
            cmd,
            check=False,  # Don't raise exception, handle manually
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Log full command output
        if process.stdout:
            logger.debug(f"FFMPEG stdout: {process.stdout}")
        if process.stderr:
            logger.debug(f"FFMPEG stderr: {process.stderr}")
            
        # Check return code
        if process.returncode != 0:
            logger.error(f"FFMPEG failed with return code {process.returncode}")
            if process.stderr:
                logger.error(f"FFMPEG error: {process.stderr}")
            return False
        
        # Check if the output file exists and has size > 0
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"Successfully converted audio to AssemblyAI format: {output_path} (size: {os.path.getsize(output_path)} bytes)")
            return True
        else:
            logger.error("FFMPEG process completed but output file is missing or empty")
            return False
            
    except subprocess.SubprocessError as e:
        logger.error(f"Subprocess error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error converting audio: {str(e)}", exc_info=True)
        return False
