import subprocess
import random
import hashlib

################################################################################
# Process URLs file, download and adjust aspect ratio
################################################################################
def get_urls(input_file_path):
    """
    Extracts a list of URLs from a given text file.

    Args:
        input_file_path (str): Path to the file containing URLs.

    Returns:
        list: A list of URLs starting with "https://".
    """
    with open(input_file_path, "r") as file:
        lines = file.readlines()        
    return [line.strip() for line in lines if line.startswith("https://")]

def process_video_urls(INPUT_DIR, DOWNLOAD_URLS, VIDEO_URLS, TEMP_DIR, PROJECT_DIR, ASPECT_RATIOS):
    """
    Downloads videos from URLs and processes them to different aspect ratios.

    Args:
        INPUT_DIR (Path): Path to the input directory.
        DOWNLOAD_URLS (bool): Flag to determine if URLs should be downloaded.
        VIDEO_URLS (str): Path to the file containing video URLs.
        TEMP_DIR (Path): Path to the temporary directory for downloads.
        PROJECT_DIR (Path): Path to the project directory.
        ASPECT_RATIOS (list): List of aspect ratios to process the videos into.
    """
    video_files = list(INPUT_DIR.glob("*/*.mp4"))
    if len(video_files) == 0 or DOWNLOAD_URLS:
        urls = get_urls(VIDEO_URLS)
        for url in urls:
            try:
                subprocess.run(['yt-dlp', '-P', TEMP_DIR, url], check=True)
            except subprocess.CalledProcessError:
                print(f"Unable to download: {url}")
        
        for video in list(TEMP_DIR.glob("*")):
            temp_video_path = PROJECT_DIR / video
            unique_id = get_file_unique_id(temp_video_path)
            for aspect_ratio in ASPECT_RATIOS:
                aspect_ratio_dir = PROJECT_DIR / "input" / aspect_ratio
                aspect_ratio_dir.mkdir(exist_ok=True)
                final_input_file_path = INPUT_DIR / f"{aspect_ratio}" / f"{unique_id}.mp4"
                if not final_input_file_path.exists():
                    ffmpeg_command = get_ffmpeg_command(temp_video_path, final_input_file_path, aspect_ratio)
                    subprocess.run(ffmpeg_command, check=True)
        
        for file in TEMP_DIR.iterdir():
            if file.is_file():
                file.unlink()

################################################################################
# Clip and Concat Helpers
################################################################################
def get_video_duration(filepath):
    """
    Retrieves the duration of a video file in seconds.

    Args:
        filepath (Path): Path to the video file.

    Returns:
        float: Duration of the video in seconds.
    """
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
         "-of", "default=noprint_wrappers=1:nokey=1", str(filepath)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
        text=True
    )
    return float(result.stdout.strip())

def extract_random_clip(filepath, duration, clip_path):
    """
    Extracts a random clip from a video file.

    Args:
        filepath (Path): Path to the original video file.
        duration (float): Duration of the original video in seconds.
        clip_path (Path): Path where the extracted clip will be saved.

    Returns:
        float: Duration of the extracted clip.
    """
    start_time = random.uniform(0, duration - 2)
    clip_duration = random.uniform(1, 2)

    subprocess.run([
        "ffmpeg", "-y", "-ss", str(start_time), "-i", str(filepath),
        "-t", str(clip_duration), "-an", "-vf", "fps=30",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p", str(clip_path)
    ], check=True)

    return clip_duration

def get_file_unique_id(file_path):
    """
    Generates a unique identifier for a file based on its SHA-256 hash.

    Args:
        file_path (Path): Path to the file.

    Returns:
        str: A unique identifier based on the last 10 characters of the hash.
    """
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256()
        
        while chunk := f.read(8192):
            file_hash.update(chunk)
    
    hash_hex = file_hash.hexdigest()
    
    return hash_hex[-10:]

def get_ffmpeg_command(input_file, output_file, aspect_ratio):
    """
    Constructs an FFmpeg command to convert a video to a specified aspect ratio.

    Args:
        input_file (Path): Path to the input video file.
        output_file (Path): Path where the output video will be saved.
        aspect_ratio (str): The target aspect ratio ("9-16" or "1-1").

    Returns:
        list: A list containing the FFmpeg command.
    """
    if aspect_ratio == "9-16":
        return [
            'ffmpeg', '-i', input_file, '-vf',
            "split[original][copy];"
            "[copy]scale=1080:1920,boxblur=luma_radius=min(1080\\,1920)/20:luma_power=1[blurred];"
            "[original]scale='if(gt(a,9/16),1080,-2)':'if(gt(a,9/16),-2,1920)'[scaled];"
            "[blurred][scaled]overlay=(W-w)/2:(H-h)/2,setsar=1",
            '-c:a', 'copy', output_file
        ]
    elif aspect_ratio == "1-1":
        return [
            'ffmpeg', '-i', input_file, '-vf',
            "split[original][copy];"
            "[copy]scale=1080:1080,boxblur=luma_radius=min(1080\\,1080)/20:luma_power=1[blurred];"
            "[original]scale='if(gt(a,1),1080,-2)':'if(gt(a,1),-2,1080)'[scaled];"
            "[blurred][scaled]overlay=(W-w)/2:(H-h)/2,setsar=1",
            '-c:a', 'copy', output_file
        ]

def clip_and_concat_videos(INPUT_DIR, ASPECT_RATIO, OUTPUT_DURATION, TEMP_DIR, OUTPUT_DIR):
    """
    Clips random segments from videos and concatenates them into a single video.

    Args:
        INPUT_DIR (Path): Path to the directory containing input videos.
        ASPECT_RATIO (str): Aspect ratio of the videos to process.
        OUTPUT_DURATION (int): Total duration of the output video in seconds.
        TEMP_DIR (Path): Path to the temporary directory for clips.
        OUTPUT_DIR (Path): Path to the directory where the final video will be saved.
    """
    video_files = list(INPUT_DIR.glob(f"{ASPECT_RATIO}/*.mp4"))
    selected_files = set()
    clip_paths = []

    total_duration = 0
    while total_duration <= OUTPUT_DURATION:
        file = random.choice(video_files)
        if file in selected_files:
            continue

        selected_files.add(file)
        clip_path = TEMP_DIR / f"clip_{len(selected_files)}.mp4"

        try:
            duration = get_video_duration(file)
            if duration >= 2:
                clip_duration = extract_random_clip(file, duration, clip_path)
                print(clip_duration)
                clip_paths.append(clip_path)
                total_duration += clip_duration
        except Exception:
            continue

    random.shuffle(clip_paths)
    concat_list_path = TEMP_DIR / "concat_list.txt"

    with open(concat_list_path, "w") as f:
        for clip in clip_paths:
            f.write(f"file '{clip.resolve()}'\n")

    output_file = OUTPUT_DIR / "output.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list_path),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-an", output_file
    ], check=True)

    for file in TEMP_DIR.iterdir():
        if file.is_file():
            file.unlink()
