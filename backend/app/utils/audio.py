"""Audio processing utilities."""

import os
import subprocess
from typing import Dict, Optional

from structlog import get_logger

# Optional ffmpeg import
try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False
    ffmpeg = None

logger = get_logger(__name__)


async def validate_audio_file(file_path: str) -> Dict:
    """
    Validate and get information about an audio/video file.

    Returns:
        Dict with duration, sample_rate, channels, etc.
    """
    try:
        # Use ffprobe to get audio information
        probe = ffmpeg.probe(file_path)

        # Get audio stream info
        audio_stream = None
        for stream in probe['streams']:
            if stream['codec_type'] == 'audio':
                audio_stream = stream
                break

        if not audio_stream:
            raise ValueError("No audio stream found in file")

        # Extract basic info
        duration = float(probe['format']['duration'])
        size_bytes = int(probe['format']['size'])

        info = {
            "duration": duration,
            "size_bytes": size_bytes,
            "format": probe['format']['format_name'],
            "bitrate": int(probe['format'].get('bit_rate', 0)),
        }

        # Audio-specific info
        if audio_stream:
            info.update({
                "sample_rate": int(audio_stream.get('sample_rate', 0)),
                "channels": int(audio_stream.get('channels', 0)),
                "codec": audio_stream.get('codec_name', 'unknown'),
            })

        logger.info("Audio file validated", file_path=file_path, info=info)
        return info

    except Exception as e:
        logger.error("Audio validation failed", file_path=file_path, error=str(e))
        raise ValueError(f"Invalid audio file: {str(e)}")


def extract_audio_from_video(
    video_path: str,
    audio_path: str,
    sample_rate: int = 16000
) -> str:
    """
    Extract audio from video file using ffmpeg.

    Args:
        video_path: Path to input video file
        audio_path: Path for output audio file
        sample_rate: Target sample rate (16kHz for Whisper)

    Returns:
        Path to extracted audio file
    """
    if not FFMPEG_AVAILABLE:
        raise ValueError("ffmpeg-python not installed. Install with: pip install ffmpeg-python")
        
    try:
        logger.info("Extracting audio from video", video_path=video_path, audio_path=audio_path)

        # FFmpeg command to extract audio
        stream = ffmpeg.input(video_path)
        stream = ffmpeg.output(
            stream,
            audio_path,
            acodec='pcm_s16le',  # 16-bit PCM
            ar=sample_rate,      # Sample rate
            ac=1,                # Mono channel
            loglevel='error'     # Reduce ffmpeg output
        )

        # Run the command
        ffmpeg.run(stream, overwrite_output=True)

        logger.info("Audio extraction completed", audio_path=audio_path)
        return audio_path

    except Exception as e:
        logger.error("Audio extraction failed", video_path=video_path, error=str(e))
        raise


async def split_audio_into_chunks(
    audio_path: str,
    output_dir: str,
    chunk_duration: int = 300,  # 5 minutes
    overlap: int = 2            # 2 seconds overlap
) -> list:
    """
    Split audio file into smaller chunks for parallel processing.

    Args:
        audio_path: Path to input audio file
        output_dir: Directory to save chunks
        chunk_duration: Duration of each chunk in seconds
        overlap: Overlap between chunks in seconds

    Returns:
        List of chunk file paths
    """
    if not FFMPEG_AVAILABLE:
        raise ValueError("ffmpeg-python not installed. Install with: pip install ffmpeg-python")
        
    try:
        # Get audio duration
        info = await validate_audio_file(audio_path)
        duration = info["duration"]

        if duration <= chunk_duration:
            # No need to split
            return [audio_path]

        logger.info(
            "Splitting audio into chunks",
            audio_path=audio_path,
            duration=duration,
            chunk_duration=chunk_duration
        )

        chunks = []
        start_time = 0

        while start_time < duration:
            end_time = min(start_time + chunk_duration, duration)

            # Create chunk filename
            chunk_num = len(chunks) + 1
            chunk_path = os.path.join(output_dir, f"chunk_{chunk_num:03d}.wav")

            # Extract chunk
            stream = ffmpeg.input(audio_path, ss=start_time, t=chunk_duration)
            stream = ffmpeg.output(
                stream,
                chunk_path,
                acodec='pcm_s16le',
                ar=16000,
                ac=1,
                loglevel='error'
            )

            ffmpeg.run(stream, overwrite_output=True)
            chunks.append(chunk_path)

            # Move to next chunk with overlap
            start_time += chunk_duration - overlap

            # Avoid infinite loop
            if start_time >= duration:
                break

        logger.info("Audio splitting completed", chunks_count=len(chunks))
        return chunks

    except Exception as e:
        logger.error("Audio splitting failed", audio_path=audio_path, error=str(e))
        raise


def convert_audio_format(
    input_path: str,
    output_path: str,
    target_format: str = "wav",
    sample_rate: int = 16000
) -> str:
    """
    Convert audio file to different format.

    Args:
        input_path: Input audio file path
        output_path: Output audio file path
        target_format: Target format (wav, mp3, etc.)
        sample_rate: Target sample rate

    Returns:
        Path to converted file
    """
    if not FFMPEG_AVAILABLE:
        raise ValueError("ffmpeg-python not installed. Install with: pip install ffmpeg-python")
        
    try:
        logger.info(
            "Converting audio format",
            input_path=input_path,
            output_path=output_path,
            format=target_format
        )

        stream = ffmpeg.input(input_path)
        stream = ffmpeg.output(
            stream,
            output_path,
            ar=sample_rate,
            ac=1,  # Mono
            loglevel='error'
        )

        ffmpeg.run(stream, overwrite_output=True)

        logger.info("Audio conversion completed", output_path=output_path)
        return output_path

    except Exception as e:
        logger.error("Audio conversion failed", input_path=input_path, error=str(e))
        raise