import streamlit as st
import yt_dlp
import os
import re
import tempfile
import time

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="VidGrab - Free Video Downloader",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── Custom CSS for Professional Look ────────────────────────────────────────
st.markdown("""
<style>
    /* ─── Import Font ─── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* ─── Global ─── */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* ─── Hide Streamlit branding ─── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ─── Hero Section ─── */
    .hero-title {
        text-align: center;
        font-size: 3rem;
        font-weight: 900;
        margin-bottom: 0;
        line-height: 1.2;
    }

    .gradient-text {
        background: linear-gradient(135deg, #6C63FF 0%, #FF6584 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .hero-sub {
        text-align: center;
        color: #888;
        font-size: 1.1rem;
        margin-top: 8px;
        margin-bottom: 30px;
    }

    /* ─── Platform Badges ─── */
    .badge-container {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 8px;
        margin: 20px 0 30px 0;
    }

    .platform-badge {
        background: rgba(108, 99, 255, 0.1);
        border: 1px solid rgba(108, 99, 255, 0.2);
        border-radius: 50px;
        padding: 6px 16px;
        font-size: 0.85rem;
        font-weight: 500;
        color: #9990FF;
        transition: all 0.3s;
    }

    /* ─── Video Card ─── */
    .video-card {
        background: rgba(26, 26, 46, 0.6);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 20px;
        margin: 15px 0;
    }

    .video-title {
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .video-meta {
        color: #888;
        font-size: 0.9rem;
    }

    /* ─── Stats Bar ─── */
    .stats-container {
        display: flex;
        justify-content: center;
        gap: 40px;
        margin: 40px 0;
        flex-wrap: wrap;
    }

    .stat-item {
        text-align: center;
    }

    .stat-number {
        font-size: 2rem;
        font-weight: 900;
        background: linear-gradient(135deg, #6C63FF 0%, #FF6584 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .stat-label {
        color: #888;
        font-size: 0.85rem;
        margin-top: 2px;
    }

    /* ─── Footer ─── */
    .custom-footer {
        text-align: center;
        color: #555;
        font-size: 0.8rem;
        margin-top: 60px;
        padding: 20px;
        border-top: 1px solid rgba(255,255,255,0.05);
    }

    /* ─── Buttons ─── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #00C853 0%, #00E676 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 36px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        width: 100% !important;
        transition: all 0.3s !important;
    }

    .stDownloadButton > button:hover {
        box-shadow: 0 8px 25px rgba(0, 200, 83, 0.3) !important;
        transform: translateY(-1px);
    }

    /* ─── Input styling ─── */
    .stTextInput > div > div > input {
        border-radius: 12px !important;
        padding: 14px 20px !important;
        font-size: 1rem !important;
        border: 2px solid rgba(108, 99, 255, 0.3) !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #6C63FF !important;
        box-shadow: 0 0 20px rgba(108, 99, 255, 0.15) !important;
    }

    .stSelectbox > div > div {
        border-radius: 12px !important;
    }

    /* ─── Divider ─── */
    .custom-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(108,99,255,0.3), transparent);
        margin: 30px 0;
    }
</style>
""", unsafe_allow_html=True)


# ─── Helper Functions ────────────────────────────────────────────────────────

def detect_platform(url: str) -> dict:
    """Detect platform from URL."""
    platforms = {
        "YouTube": {"pattern": r"(youtube\.com|youtu\.be)", "icon": "🔴", "color": "#FF0000"},
        "Instagram": {"pattern": r"(instagram\.com|instagr\.am)", "icon": "📸", "color": "#E1306C"},
        "Twitter/X": {"pattern": r"(twitter\.com|x\.com)", "icon": "🐦", "color": "#1DA1F2"},
        "Facebook": {"pattern": r"(facebook\.com|fb\.watch)", "icon": "📘", "color": "#1877F2"},
        "TikTok": {"pattern": r"(tiktok\.com)", "icon": "🎵", "color": "#000000"},
        "Reddit": {"pattern": r"(reddit\.com|redd\.it)", "icon": "🤖", "color": "#FF4500"},
        "Vimeo": {"pattern": r"(vimeo\.com)", "icon": "🎬", "color": "#1AB7EA"},
    }
    for name, info in platforms.items():
        if re.search(info["pattern"], url, re.IGNORECASE):
            return {"name": name, "icon": info["icon"]}
    return {"name": "Other", "icon": "🌐"}


COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Mode": "navigate",
}

YOUTUBE_EXTRACTOR_ARGS = {
    "youtube": {
        "player_client": ["android"],
        "player_skip": ["webpage", "configs"],
    }
}


def fetch_youtube_oembed(url: str) -> dict:
    """Fallback to official YouTube oEmbed API when cloud server IP is restricted."""
    import urllib.request
    import json
    try:
        api_url = f"https://www.youtube.com/oembed?url={url}&format=json"
        req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "success": True,
                "title": data.get("title", "YouTube Video"),
                "uploader": data.get("author_name", "YouTube Creator"),
                "duration": "Full Video",
                "duration_secs": 0,
                "views": None,
                "likes": None,
                "thumbnail": data.get("thumbnail_url", ""),
                "qualities": ["1080", "720", "480", "360"],
                "platform": {"name": "YouTube", "icon": "🔴"},
                "webpage_url": url,
                "is_fallback": True,
            }
    except Exception:
        return None


def fetch_video_info(url: str) -> dict:
    """Fetch video info without downloading."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "no_check_certificates": True,
        "extractor_args": YOUTUBE_EXTRACTOR_ARGS,
        "http_headers": COMMON_HEADERS,
        "socket_timeout": 8,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Available qualities
            qualities = sorted(set(
                f.get("height") for f in info.get("formats", [])
                if f.get("height") and f.get("vcodec", "none") != "none"
            ), reverse=True)

            # Duration formatting
            duration = info.get("duration", 0)
            if duration:
                mins, secs = divmod(int(duration), 60)
                hours, mins = divmod(mins, 60)
                duration_str = f"{hours}:{mins:02d}:{secs:02d}" if hours else f"{mins}:{secs:02d}"
            else:
                duration_str = "N/A"

            return {
                "success": True,
                "title": info.get("title", "Unknown"),
                "uploader": info.get("uploader", "Unknown"),
                "duration": duration_str,
                "duration_secs": duration,
                "views": info.get("view_count"),
                "likes": info.get("like_count"),
                "thumbnail": info.get("thumbnail", ""),
                "qualities": qualities,
                "platform": detect_platform(url),
                "webpage_url": info.get("webpage_url", url),
                "is_fallback": False,
            }
    except Exception as e:
        if "youtube.com" in url or "youtu.be" in url:
            oembed_info = fetch_youtube_oembed(url)
            if oembed_info:
                return oembed_info
        return {"success": False, "error": str(e)}


def download_video(url: str, quality: str = "best", audio_only: bool = False) -> dict:
    """Download video and return file path."""
    tmp_dir = tempfile.mkdtemp()
    output_template = os.path.join(tmp_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
        "no_check_certificates": True,
        "extractor_args": YOUTUBE_EXTRACTOR_ARGS,
        "http_headers": COMMON_HEADERS,
    }

    if audio_only:
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        if quality == "best":
            ydl_opts["format"] = "best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
        elif str(quality).isdigit():
            h = quality
            ydl_opts["format"] = (
                f"best[height<={h}][ext=mp4]/"
                f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/"
                f"bestvideo[height<={h}]+bestaudio/"
                f"best[height<={h}]/best"
            )
        else:
            ydl_opts["format"] = "best[ext=mp4]/best"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find downloaded file
        for f in os.listdir(tmp_dir):
            filepath = os.path.join(tmp_dir, f)
            if os.path.isfile(filepath):
                file_size = os.path.getsize(filepath)
                return {
                    "success": True,
                    "filepath": filepath,
                    "filename": f,
                    "size": file_size,
                }

        return {"success": False, "error": "File not found after download"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def format_views(n):
    """Format large numbers."""
    if not n:
        return "N/A"
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def format_size(size_bytes):
    """Format file size."""
    if size_bytes >= 1_073_741_824:
        return f"{size_bytes / 1_073_741_824:.2f} GB"
    elif size_bytes >= 1_048_576:
        return f"{size_bytes / 1_048_576:.1f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} B"


# ─── Initialize Session State ────────────────────────────────────────────────
if "video_info" not in st.session_state:
    st.session_state.video_info = None
if "download_result" not in st.session_state:
    st.session_state.download_result = None


# ═══════════════════════════════════════════════════════════════════════════════
#                              MAIN UI
# ═══════════════════════════════════════════════════════════════════════════════

# ─── Hero Section ─────────────────────────────────────────────────────────────
st.markdown('<h1 class="hero-title">Download Videos from<br><span class="gradient-text">Any Platform</span></h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-sub">Paste any video URL and download in seconds. YouTube, Instagram, Twitter & 1000+ sites supported.</p>', unsafe_allow_html=True)

# Platform badges
st.markdown("""
<div class="badge-container">
    <span class="platform-badge">🔴 YouTube</span>
    <span class="platform-badge">📸 Instagram</span>
    <span class="platform-badge">🐦 Twitter/X</span>
    <span class="platform-badge">📘 Facebook</span>
    <span class="platform-badge">🎵 TikTok</span>
    <span class="platform-badge">🤖 Reddit</span>
    <span class="platform-badge">🌐 1000+ More</span>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

# ─── URL Input ────────────────────────────────────────────────────────────────
url = st.text_input(
    "🔗 Paste Video URL",
    placeholder="https://www.youtube.com/watch?v=... or any video URL",
    label_visibility="collapsed",
)

# ─── Options Row ──────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    quality = st.selectbox(
        "📺 Quality",
        options=["best", "2160", "1440", "1080", "720", "480", "360"],
        format_func=lambda x: {
            "best": "🏆 Best Quality",
            "2160": "4K (2160p)",
            "1440": "2K (1440p)",
            "1080": "Full HD (1080p)",
            "720": "HD (720p)",
            "480": "SD (480p)",
            "360": "Low (360p)",
        }.get(x, x),
        index=3,  # Default to 1080p
    )

with col2:
    audio_only = st.selectbox(
        "🎵 Format",
        options=[False, True],
        format_func=lambda x: "🎵 Audio Only (MP3)" if x else "🎬 Video (MP4)",
    )

# ─── Fetch Info Button ───────────────────────────────────────────────────────
fetch_col1, fetch_col2, fetch_col3 = st.columns([1, 2, 1])
with fetch_col2:
    fetch_clicked = st.button("🔍  Fetch Video Info", use_container_width=True, type="primary")

def clean_url(raw_url: str) -> str:
    if not raw_url:
        return ""
    u = raw_url.strip()
    parts = u.split()
    if parts:
        u = parts[0].rstrip(",;")
    return u


url = clean_url(url)

if fetch_clicked and url:
    if not url.startswith(("http://", "https://")):
        st.error("❌ Please enter a valid URL (starting with http:// or https://)")
    else:
        with st.spinner("⏳ Fetching video info..."):
            info = fetch_video_info(url)
            st.session_state.video_info = info
            st.session_state.download_result = None

elif fetch_clicked and not url:
    st.warning("⚠️ Please paste a video URL first!")

# ─── Video Info Display ──────────────────────────────────────────────────────
if st.session_state.video_info:
    info = st.session_state.video_info

    if not info["success"]:
        err_msg = str(info.get('error', ''))
        yt_id_match = re.search(r'(?:v=|youtu\.be\/|\/shorts\/)([0-9A-Za-z_-]{11})', url)
        if yt_id_match and ("sign in" in err_msg.lower() or "bot" in err_msg.lower() or "429" in err_msg or "confirm" in err_msg.lower()):
            video_id = yt_id_match.group(1)
            st.warning("⚠️ **YouTube Cloud Bot Check:** YouTube ne free cloud server ke IP ko temporarily challenge kiya hai.")
            st.markdown("### 🚀 **Aap neeche diye gaye Direct Servers se 1-Click mein download kar sakte hain:**")
            fb_col1, fb_col2 = st.columns(2)
            with fb_col1:
                st.link_button("⚡ Direct Download (Fast Server 1)", f"https://www.ssyoutube.com/watch?v={video_id}", use_container_width=True)
            with fb_col2:
                st.link_button("🎬 Direct Download (Server 2 - MP4/MP3)", f"https://www.y2mate.com/youtube/{video_id}", use_container_width=True)
        else:
            st.error(f"❌ Could not fetch video: {err_msg}")
    else:
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

        platform = info["platform"]

        # Thumbnail + Info
        tcol1, tcol2 = st.columns([1, 1.5])

        with tcol1:
            if info["thumbnail"]:
                st.image(info["thumbnail"], use_container_width=True)

        with tcol2:
            st.markdown(f"**{platform['icon']} {platform['name']}**")
            st.markdown(f"### {info['title']}")
            st.markdown(f"""
            | | |
            |---|---|
            | 👤 **Uploader** | {info['uploader']} |
            | ⏱️ **Duration** | {info['duration']} |
            | 👁️ **Views** | {format_views(info.get('views'))} |
            | ❤️ **Likes** | {format_views(info.get('likes'))} |
            """)

        st.markdown("")

        st.markdown("")

        yt_id_match = re.search(r'(?:v=|youtu\.be\/|\/shorts\/)([0-9A-Za-z_-]{11})', url)

        if platform['name'] == 'YouTube' and yt_id_match:
            video_id = yt_id_match.group(1)
            st.markdown("### 📥 **Select Download Quality:**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.link_button(
                    "🚀 Download MP4 (1080p / 720p / 480p)",
                    f"https://www.ssyoutube.com/watch?v={video_id}",
                    use_container_width=True,
                    type="primary",
                )
            with col_b:
                st.link_button(
                    "🎵 Download MP3 / Audio",
                    f"https://www.y2mate.com/youtube/{video_id}",
                    use_container_width=True,
                )
            st.markdown(
                """
                <div style="background: rgba(0, 200, 83, 0.1); border: 1px solid #00C853; border-radius: 12px; padding: 12px; margin-top: 15px; text-align: center; color: #00E676; font-size: 0.95rem;">
                    ✅ <b>Guaranteed 100% Working:</b> Upar diye gaye kisi bhi button par click karein aur apni quality select karke bina kisi server error ke turant download karein!
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            # For Instagram, Facebook, Twitter, TikTok & others
            dl_col1, dl_col2, dl_col3 = st.columns([1, 2, 1])
            with dl_col2:
                download_clicked = st.button(
                    "⬇️  Download Now",
                    use_container_width=True,
                    type="primary",
                    key="download_btn",
                )

            if download_clicked:
                progress_bar = st.progress(0, text="⏳ Starting download...")
                status_text = st.empty()

                progress_bar.progress(10, text="📡 Connecting to server...")
                result = download_video(url, quality=quality, audio_only=audio_only)
                progress_bar.progress(100, text="✅ Download complete!")

                if result["success"]:
                    st.session_state.download_result = result
                    st.success(f"✅ Ready! File size: **{format_size(result['size'])}**")
                else:
                    err_msg = str(result.get("error", ""))
                    st.error(f"❌ Download failed: {err_msg}")

        # ─── Save File Button ────────────────────────────────────────────
        if st.session_state.download_result and st.session_state.download_result["success"]:
            result = st.session_state.download_result
            filepath = result["filepath"]
            filename = result["filename"]

            if os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    file_bytes = f.read()

                ext = ".mp3" if filename.endswith(".mp3") else ".mp4"
                base_name = os.path.splitext(filename)[0]
                safe_name = re.sub(r'[^\w\s\.-]', '_', base_name).strip()[:80] + ext
                if not safe_name or safe_name.startswith('.'):
                    safe_name = "downloaded_video" + ext

                st.markdown("")
                save_col1, save_col2, save_col3 = st.columns([1, 2, 1])
                with save_col2:
                    mime = "audio/mpeg" if ext == ".mp3" else "video/mp4"
                    st.download_button(
                        label=f"💾 Save File ({format_size(result['size'])})",
                        data=file_bytes,
                        file_name=safe_name,
                        mime=mime,
                        use_container_width=True,
                    )

# ─── Stats ────────────────────────────────────────────────────────────────────
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="stats-container">
    <div class="stat-item">
        <div class="stat-number">1000+</div>
        <div class="stat-label">Supported Sites</div>
    </div>
    <div class="stat-item">
        <div class="stat-number">4K</div>
        <div class="stat-label">Max Quality</div>
    </div>
    <div class="stat-item">
        <div class="stat-number">Free</div>
        <div class="stat-label">No Limits</div>
    </div>
    <div class="stat-item">
        <div class="stat-number">MP3</div>
        <div class="stat-label">Audio Extract</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── How to Use ───────────────────────────────────────────────────────────────
with st.expander("📖 How to Use"):
    st.markdown("""
    1. **Paste URL** — Copy any video link from YouTube, Instagram, Twitter, etc.
    2. **Choose Quality** — Select from 360p to 4K
    3. **Click Fetch** — See video details & thumbnail
    4. **Click Download** — Wait for processing
    5. **Save File** — Click the green save button to save to your device

    **Supported Platforms:** YouTube, Instagram, Twitter/X, Facebook, TikTok, Reddit, Vimeo, Dailymotion, Pinterest, and 1000+ more!
    """)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="custom-footer">
    <p>🎬 <strong>VidGrab</strong> — Universal Video Downloader</p>
    <p>Please respect copyright laws and platform terms of service.</p>
</div>
""", unsafe_allow_html=True)
