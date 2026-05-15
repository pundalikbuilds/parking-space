from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pathlib import Path
import subprocess
import sys

app = FastAPI()

# Base directory
base_dir = Path(__file__).resolve().parent
media_dir = base_dir / "media"


class VideoRequest(BaseModel):
    video_name: str
    camera_name: str = "cam1"


@app.post("/play-video")
async def play_video(request: VideoRequest):
    """
    Receive a POST request with video name and camera name,
    search for the video in the media folder, and play it with main.py.
    """
    video_name = request.video_name.strip()
    camera_name = request.camera_name.strip()

    if not video_name:
        raise HTTPException(status_code=400, detail="video_name cannot be empty")

    # Search for video in media folder
    video_path = None
    
    # Try exact match first
    for ext in [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"]:
        candidate = media_dir / f"{video_name}{ext}"
        if candidate.exists():
            video_path = candidate
            break
    
    # If not found, try case-insensitive search
    if video_path is None:
        try:
            for file in media_dir.iterdir():
                if file.is_file() and file.name.lower() == video_name.lower():
                    video_path = file
                    break
                # Also try matching without extension
                if file.is_file() and file.stem.lower() == video_name.lower():
                    video_path = file
                    break
        except FileNotFoundError:
            pass

    if video_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"Video '{video_name}' not found in {media_dir}"
        )

    try:
        # Run main.py with the video path and camera name
        # Pass the video path as environment variable or argument
        result = subprocess.run(
            [
                sys.executable,
                str(base_dir / "main.py"),
                str(video_path),
                camera_name
            ],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        if result.returncode != 0:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "Failed to play video",
                    "error": result.stderr
                }
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": f"Video '{video_name}' played successfully",
                "video_path": str(video_path),
                "camera_name": camera_name
            }
        )

    except subprocess.TimeoutExpired:
        return JSONResponse(
            status_code=504,
            content={
                "status": "error",
                "message": "Video playback timeout"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "An error occurred",
                "error": str(e)
            }
        )


@app.get("/videos")
async def list_videos():
    """
    List all available videos in the media folder.
    """
    try:
        videos = []
        for file in media_dir.iterdir():
            if file.is_file() and file.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']:
                videos.append({
                    "name": file.name,
                    "stem": file.stem,
                    "size": file.stat().st_size
                })
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "count": len(videos),
                "videos": videos
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Failed to list videos",
                "error": str(e)
            }
        )


@app.get("/health")
async def health():
    """
    Health check endpoint.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "media_dir": str(media_dir),
            "media_dir_exists": media_dir.exists()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
