import os
import shutil
import tempfile
from urllib.parse import urlparse

from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)

ALLOWED_ORIGINS = [
    "https://toolsmediadownload.online",
    "https://www.toolsmediadownload.online",
]

CORS(app, resources={r"/download": {"origins": ALLOWED_ORIGINS}})

INSTAGRAM_HOSTS = {
    "instagram.com",
    "www.instagram.com",
}

FACEBOOK_HOSTS = {
    "facebook.com",
    "www.facebook.com",
    "m.facebook.com",
    "web.facebook.com",
    "fb.watch",
    "fb.com",
    "www.fb.com",
}

PINTEREST_HOSTS = {
    "pinterest.com",
    "www.pinterest.com",
    "m.pinterest.com",
    "in.pinterest.com",
    "pin.it",
}


def get_platform(url):
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()

        if parsed.scheme != "https":
            return None

        if host in INSTAGRAM_HOSTS:
            if parsed.path.startswith(("/p/", "/reel/", "/reels/", "/tv/")):
                return "instagram"

        if host in FACEBOOK_HOSTS:
            if parsed.path != "/":
                return "facebook"

        if host in PINTEREST_HOSTS:
            if host == "pin.it" or parsed.path.startswith("/pin/"):
                return "pinterest"

        return None

    except Exception:
        return None


@app.route("/", methods=["GET"])
def home():
    return "Instagram, Facebook and Pinterest downloader backend is running!"


@app.route("/download", methods=["POST"])
def download_video():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    platform = get_platform(url)

    if not platform:
        return jsonify({
            "error": "Valid public Instagram, Facebook ya Pinterest video link dein."
        }), 400

    temp_dir = tempfile.mkdtemp(prefix="media_download_")

    try:
        options = {
            "outtmpl": os.path.join(temp_dir, "video.%(ext)s"),
            "format": "best[ext=mp4]/best",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 30,
            "max_filesize": 100 * 1024 * 1024,
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        files = [
            os.path.join(temp_dir, name)
            for name in os.listdir(temp_dir)
            if os.path.isfile(os.path.join(temp_dir, name))
        ]

        if not files:
            raise RuntimeError("Video file nahi mili.")

        video_path = files[0]
        extension = os.path.splitext(video_path)[1] or ".mp4"
        filename = f"{platform}_video{extension}"

        response = send_file(
            video_path,
            as_attachment=True,
            download_name=filename,
        )

        response.call_on_close(
            lambda: shutil.rmtree(temp_dir, ignore_errors=True)
        )

        return response

    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)

        app.logger.exception("Media download failed for platform: %s", platform)

        return jsonify({
            "error": (
                "Video download nahi ho saki. Public link check karein. "
                "Kuch videos login, privacy ya platform restrictions ki "
                "wajah se available nahi hoti."
            )
        }), 400


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
