import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, ID3NoHeaderError
from utils.logger import get_logger

logger = get_logger("metadata_reader")


def get_mp3_metadata(file_path: str) -> dict:
    """
    Reads metadata from an MP3 file using mutagen.
    Returns a dict with:
        title (str | None)
        artist (str | None)
        album (str | None)
        duration (float)
        bitrate (int) - in kbps
        cover_art (bytes | None)
    """
    metadata = {
        "title": None,
        "artist": None,
        "album": None,
        "duration": 0.0,
        "bitrate": 0,
        "cover_art": None,
    }

    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return metadata

    try:
        audio = MP3(file_path)
        metadata["duration"] = audio.info.length
        metadata["bitrate"] = audio.info.bitrate // 1000  # convert to kbps
    except Exception as e:
        logger.error(f"Error reading audio info for {file_path}: {e}")

    try:
        tags = ID3(file_path)
        # TIT2 is title
        if tags.get("TIT2"):
            metadata["title"] = str(tags.get("TIT2").text[0])
        # TPE1 is lead performer/artist
        if tags.get("TPE1"):
            metadata["artist"] = str(tags.get("TPE1").text[0])
        # TALB is album title
        if tags.get("TALB"):
            metadata["album"] = str(tags.get("TALB").text[0])

        # Look for cover art in APIC frames
        for key in tags.keys():
            if key.startswith("APIC"):
                metadata["cover_art"] = tags[key].data
                break
    except ID3NoHeaderError:
        logger.debug(f"No ID3 tags found for {file_path}")
    except Exception as e:
        logger.error(f"Error reading ID3 tags for {file_path}: {e}")

    return metadata
