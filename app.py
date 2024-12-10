from dotenv import load_dotenv
import os
from pathlib import Path
import utils



def main():
    # Load environment variables from .env file
    load_dotenv()
    OUTPUT_DURATION = int(os.getenv("OUTPUT_DURATION", 8))

    PROJECT_DIR = Path.cwd()

    INPUT_DIR = Path(os.getenv("INPUT_DIR", "./input/"))
    INPUT_DIR.mkdir(exist_ok=True)

    TEMP_DIR = Path(os.getenv("TEMP_DIR", "./temp/"))
    TEMP_DIR.mkdir(exist_ok=True)

    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output/"))
    OUTPUT_DIR.mkdir(exist_ok=True)

    DOWNLOAD_URLS = os.getenv("DOWNLOAD_URLS", False)
    VIDEO_URLS = os.getenv("VIDEO_URLS", "./video-urls.txt")

    ASPECT_RATIOS = ["9-16", "1-1"]
    ASPECT_RATIO = os.getenv("ASPECT_RATIO", "9-16")

    utils.process_video_urls(INPUT_DIR, DOWNLOAD_URLS, VIDEO_URLS, TEMP_DIR, PROJECT_DIR, ASPECT_RATIOS)
    utils.clip_and_concat_videos(INPUT_DIR, ASPECT_RATIO, OUTPUT_DURATION, TEMP_DIR, OUTPUT_DIR)

if __name__ == "__main__":
    main()
