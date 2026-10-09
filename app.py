import os
import tempfile
from urllib.parse import urlparse

from flask import Flask, request, send_file, jsonify, after_this_request
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/download": {
            "origins": [
                "https://toolsmediadownload.online",
                "https://www.toolsmediadownload.online",
            ]
        }
    },
)

def valid_instagram_url(url):
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()

        return (
            parsed.scheme == "https"
            and host in {"instagram.com", "www.instagram.com"}
            and parsed.path.startswith(("/p/", "/reel/", "/reels/", "/tv/"))
        )
    except Exception:
        return False


@app.route("/", methods=["GET"])
def home():
    return "Instagram Downloader backend is running!"


@app.route("/download", methods=["POST"])
def download_video():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()

    if not valid_instagram_url(url):
        return jsonify({
            "error": "Valid public Instagram post ya Reel ka link dein."
        }), 400

    temp_dir = tempfile.mkdtemp(prefix="instagram_")

    try:
        options = {
            "outtmpl": os.path.join(temp_dir, "video.%(ext)s"),
            "format": "best[ext=mp4]/best",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 20,
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

        @after_this_request
        def cleanup(response):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            return response

        return send_file(
            video_path,
            as_attachment=True,
            download_name="instagram_video.mp4",
        )

    except Exception:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

        return jsonify({
            "error": (
                "Video download nahi ho saki. Link check karein; "
                "kuch Instagram posts available nahi hoti."
            )
        }), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
