from flask import Flask, jsonify, Response
import requests
import os
import base64

app = Flask(__name__)

# Character ID to image mapping (UNCHANGED)
character_map = {
    "806": "102000008.png",    # Kla
    "306": "102000006.png",    # Ford
    "906": "101000009.png",    # Paloma
    "2406": "101000016.png",   # Notora
    "1003": "102000009.png",   # Miguel
    "2306": "102000016.png",   # Alvaro
    "6306": "102000016.png",   # Awaken Alvaro
    "7506": "101000053.png",   # Rin
    "1306": "102000010.png",   # Antonio
    "2006": "102000014.png",   # Joseph
    "2106": "101000014.png",   # Shani
    "2806": "101100018.png",   # Kapella
    "7206": "102000051.png",   # Koda
    "7006": "101000049.png",   # Kassie
    "6906": "102000046.png",   # Kairos
    "6806": "102000045.png",   # Ryden
    "6706": "102000044.png",   # Ignis
    "6606": "101000028.png",   # Suzy
    "6506": "101000027.png",   # Sonia
    "6206": "102000041.png",   # Orion
    "6006": "102000040.png",   # Santino
    "5306": "101000026.png",   # Luna
    "5806": "102000039.png",   # Tatsuya
    "5606": "101000025.png",   # Iris
    "5706": "102000038.png",   # J.Biebs
    "5506": "102000037.png",   # Homer
    "5406": "102000036.png",   # Kenta
    "5206": "102000034.png",   # Nairi
    "5006": "102000033.png",   # Otho
    "4906": "102000032.png",   # Leon
    "4606": "102000030.png",   # Thiva
    "4706": "102000031.png",   # Dimitri
    "4506": "102000029.png",   # D-bee
    "4306": "102000028.png",   # Maro
    "4006": "102000025.png",   # Skyler
    "4406": "101000022.png",   # Xayne
    "4106": "102000026.png",   # Shirou
    "3806": "102000024.png",   # Chrono
    "3506": "101000020.png",   # Dasha
    "3406": "102000022.png",   # K
    "2906": "102000018.png",   # Luqueta
    "206": "101000006.png",    # Kelly
    "1506": "102000012.png",   # Hayato Yagami
    "1406": "101000023.png",   # Moco
    "2606": "101000017.png",   # Steffie
    "606": "101000008.png",    # Misha
    "706": "102000007.png",    # Maxim
    "406": "102000005.png",    # Andrew
    "7106": "101000050.png",   # Lila
    "1106": "101000010.png",   # Caroline
    "1706": "101000012.png",   # Laura
    "1806": "102000013.png",   # Rafael
    "2206": "102000015.png",   # Alok
    "2706": "102000017.png",   # Jota
    "3106": "101000019.png",   # Clu
    "3006": "102200019.png",   # Wolfrahh
    "3306": "102000021.png",   # Jai
    "4203": "102000005.png",   # Awaken Andrew
    "4806": "101000023.png",   # Awaken Moco
    "3203": "102000012.png",   # Awaken Hayato
    "2506": "101000006.png",   # Awaken Kelly
    "22016": "102000015.png",  # Awaken Alok
    "506": "101000007.png",    # Nikita
    "1906": "101000013.png",   # A124
    "7406": "102000052.png",   # Oscar
    "1206": "102000011.png",   # Wukong
    "106": "101000005.png"     # Olivia
}

# --- Repo config (env override allowed) ---
GITHUB_OWNER = os.environ.get("GITHUB_OWNER", "hackeravibhav-dot")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "character-api-vaibhav")
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")
PNG_DIR = os.environ.get("PNG_DIR", "pngs")


def resolve_filename(id_str: str):
    # Remove .bin extension if present
    if id_str.endswith(".bin"):
        id_str = id_str[:-4]

    # Character ID (3-6 digits) OR Skill ID (8-11 digits)
    if 3 <= len(id_str) <= 6:
        filename = character_map.get(id_str)
    elif 8 <= len(id_str) <= 11:
        filename = f"{id_str}.png"
    else:
        return None, "Invalid ID format"

    if not filename:
        return None, "ID not found"

    return filename, None


def fetch_png_from_private_repo(filename: str):
    """
    Fetches PNG bytes using GitHub Contents API (supports private repo).
    Requires env var: GITHUB_TOKEN
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return None, "Missing GITHUB_TOKEN (private repo needs auth)"

    path = f"{PNG_DIR}/{filename}"
    api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}?ref={GITHUB_BRANCH}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "character-api",
    }

    r = requests.get(api_url, headers=headers, timeout=15)

    if r.status_code == 404:
        return None, "File not found"
    if r.status_code == 403:
        return None, "Forbidden (check token permissions / rate limit)"
    if r.status_code != 200:
        return None, f"GitHub API error. Status: {r.status_code}"

    data = r.json()
    content_b64 = data.get("content")
    if not content_b64:
        return None, "GitHub API response missing file content"

    content_b64 = content_b64.replace("\n", "")
    try:
        img_bytes = base64.b64decode(content_b64)
    except Exception:
        return None, "Failed to decode base64 from GitHub API"

    return img_bytes, None


@app.route("/")
def home():
    return jsonify({
        "message": "Character API is working! Use /api/<id>",
        "repo_mode": "PRIVATE_ONLY (GitHub API)",
        "required_env": ["GITHUB_TOKEN"],
        "optional_env": ["GITHUB_OWNER", "GITHUB_REPO", "GITHUB_BRANCH", "PNG_DIR"]
    })


@app.route("/api/<id>")
def get_character_image(id):
    try:
        filename, err = resolve_filename(id)
        if err:
            return jsonify({"error": err}), 404

        img_bytes, ferr = fetch_png_from_private_repo(filename)
        if ferr:
            # Token missing -> 500 makes sense; file not found -> 404
            status = 500 if ferr.startswith("Missing GITHUB_TOKEN") else 404
            return jsonify({"error": ferr}), status

        resp = Response(img_bytes, content_type="image/png")
        # Cache is optional; if you want strict privacy, you can reduce max-age or remove it.
        resp.headers["Cache-Control"] = "public, max-age=86400"
        resp.headers["X-Image-Source"] = "GITHUB_API_PRIVATE"
        return resp

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timeout"}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Network error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# Vercel serverless expects 'app'
app = app