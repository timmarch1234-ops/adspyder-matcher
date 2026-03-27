import os, io, json, hashlib, subprocess, tempfile, threading, time
from pathlib import Path
from flask import Flask, request, session, redirect, render_template_string, jsonify, send_file
import requests as req
from PIL import Image
import imagehash
import anthropic
import fitz  # PyMuPDF

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "adspyder-secret-2024")

CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
PASSWORD = os.environ.get("APP_PASSWORD", "1234")
DATA_DIR = Path("/data")
DATA_DIR.mkdir(exist_ok=True)
MATCHES_DB = DATA_DIR / "learned_matches.json"
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

OUR_LINKS = [
    "https://cdn.twinklingtree.com/0000120795.jpg","https://cdn.twinklingtree.com/0003734376.mp4",
    "https://cdn.twinklingtree.com/0007851448.mp4","https://cdn.twinklingtree.com/0009241842.jpg",
    "https://cdn.twinklingtree.com/0015247910.jpg","https://cdn.twinklingtree.com/0016177243.jpg",
    "https://cdn.twinklingtree.com/0022446111.jpg","https://cdn.twinklingtree.com/0024079870.png",
    "https://cdn.twinklingtree.com/0028907319.jpg","https://cdn.twinklingtree.com/0029603524.jpg",
    "https://cdn.twinklingtree.com/0029837830.mp4","https://cdn.twinklingtree.com/0037274028.mp4",
    "https://cdn.twinklingtree.com/0040451824.mp4","https://cdn.twinklingtree.com/0041841412.jpg",
    "https://cdn.twinklingtree.com/0048009111.jpg","https://cdn.twinklingtree.com/0052964109.mp4",
    "https://cdn.twinklingtree.com/0054112437.mp4","https://cdn.twinklingtree.com/0056163627.mp4",
    "https://cdn.twinklingtree.com/0062969915.mp4","https://cdn.twinklingtree.com/0063654904.jpg",
    "https://cdn.twinklingtree.com/0072540298.jpg","https://cdn.twinklingtree.com/0077016010.jpg",
    "https://cdn.twinklingtree.com/0084760730.mp4","https://cdn.twinklingtree.com/0087874458.jpg",
    "https://cdn.twinklingtree.com/0089587168.jpg","https://cdn.twinklingtree.com/0091554960.mp4",
    "https://cdn.twinklingtree.com/0095838677.mp4","https://cdn.twinklingtree.com/0102390487.mp4",
    "https://cdn.twinklingtree.com/0112037829.jpg","https://cdn.twinklingtree.com/0117630495.jpg",
    "https://cdn.twinklingtree.com/0121067690.mp4","https://cdn.twinklingtree.com/0125510772.jpg",
    "https://cdn.twinklingtree.com/0127556440.jpg","https://cdn.twinklingtree.com/0135314784.mp4",
    "https://cdn.twinklingtree.com/0136671947.jpeg","https://cdn.twinklingtree.com/0138476075.mp4",
    "https://cdn.twinklingtree.com/0138804641.jpeg","https://cdn.twinklingtree.com/0140808204.jpg",
    "https://cdn.twinklingtree.com/0142376421.jpg","https://cdn.twinklingtree.com/0153590060.jpg",
    "https://cdn.twinklingtree.com/0168071364.mp4","https://cdn.twinklingtree.com/0180796941.mp4",
    "https://cdn.twinklingtree.com/0188858046.jpg","https://cdn.twinklingtree.com/0192369051.jpg",
    "https://cdn.twinklingtree.com/0199781071.jpg","https://cdn.twinklingtree.com/0206157875.png",
    "https://cdn.twinklingtree.com/0207922122.jpg","https://cdn.twinklingtree.com/0214524743.jpg",
    "https://cdn.twinklingtree.com/0215272334.jpg","https://cdn.twinklingtree.com/0217841955.mp4",
    "https://cdn.twinklingtree.com/0219485322.jpg","https://cdn.twinklingtree.com/0230873686.mp4",
    "https://cdn.twinklingtree.com/0231879230.jpg","https://cdn.twinklingtree.com/0235951670.jpg",
    "https://cdn.twinklingtree.com/0237897791.jpg","https://cdn.twinklingtree.com/0238025138.mp4",
    "https://cdn.twinklingtree.com/0245961664.jpg","https://cdn.twinklingtree.com/0246182918.mp4",
    "https://cdn.twinklingtree.com/0246212262.mp4","https://cdn.twinklingtree.com/0246930827.mp4",
    "https://cdn.twinklingtree.com/0248762961.jpg","https://cdn.twinklingtree.com/0249262720.jpg",
    "https://cdn.twinklingtree.com/0253082188.jpg","https://cdn.twinklingtree.com/0256536128.mp4",
    "https://cdn.twinklingtree.com/0262407805.jpg","https://cdn.twinklingtree.com/0263180373.jpg",
    "https://cdn.twinklingtree.com/0264073953.jpg","https://cdn.twinklingtree.com/0265749701.jpg",
    "https://cdn.twinklingtree.com/0273006519.mp4","https://cdn.twinklingtree.com/0273818253.jpg",
    "https://cdn.twinklingtree.com/0282927237.mp4","https://cdn.twinklingtree.com/0286560647.jpg",
    "https://cdn.twinklingtree.com/0287783631.mp4","https://cdn.twinklingtree.com/0297442840.jpg",
    "https://cdn.twinklingtree.com/0299289059.jpg","https://cdn.twinklingtree.com/0301610176.jpg",
    "https://cdn.twinklingtree.com/0303443366.jpg","https://cdn.twinklingtree.com/0304424768.jpg",
    "https://cdn.twinklingtree.com/0305355424.mp4","https://cdn.twinklingtree.com/0307753978.mp4",
    "https://cdn.twinklingtree.com/0311546059.jpg","https://cdn.twinklingtree.com/0313214523.mp4",
    "https://cdn.twinklingtree.com/0316034922.mp4","https://cdn.twinklingtree.com/0320176504.jpg",
    "https://cdn.twinklingtree.com/0325924825.jpg","https://cdn.twinklingtree.com/0327242120.jpg",
    "https://cdn.twinklingtree.com/0329423217.png","https://cdn.twinklingtree.com/0336800338.mp4",
    "https://cdn.twinklingtree.com/0337453837.mp4","https://cdn.twinklingtree.com/0338277848.mp4",
    "https://cdn.twinklingtree.com/0339975042.mp4","https://cdn.twinklingtree.com/0341739549.jpg",
    "https://cdn.twinklingtree.com/0357742623.jpg","https://cdn.twinklingtree.com/0358508815.png",
    "https://cdn.twinklingtree.com/0363282759.jpg","https://cdn.twinklingtree.com/0363521082.mp4",
    "https://cdn.twinklingtree.com/0364083626.jpg","https://cdn.twinklingtree.com/0370894202.jpg",
    "https://cdn.twinklingtree.com/0374309830.mp4","https://cdn.twinklingtree.com/0375308199.jpg",
    "https://cdn.twinklingtree.com/0378235367.jpg","https://cdn.twinklingtree.com/0378999279.jpg",
    "https://cdn.twinklingtree.com/0382166742.jpg","https://cdn.twinklingtree.com/0382324367.jpg",
    "https://cdn.twinklingtree.com/0401252872.jpg","https://cdn.twinklingtree.com/0410530330.jpg",
    "https://cdn.twinklingtree.com/0411254396.jpg","https://cdn.twinklingtree.com/0417106522.mp4",
    "https://cdn.twinklingtree.com/0419469383.jpg","https://cdn.twinklingtree.com/0419489858.jpg",
    "https://cdn.twinklingtree.com/0420630869.jpg","https://cdn.twinklingtree.com/0434061094.mp4",
    "https://cdn.twinklingtree.com/0438676331.jpg","https://cdn.twinklingtree.com/0441037053.mp4",
    "https://cdn.twinklingtree.com/0445798948.jpg","https://cdn.twinklingtree.com/0454660908.mp4",
    "https://cdn.twinklingtree.com/0461129155.mp4","https://cdn.twinklingtree.com/0461485637.jpg",
    "https://cdn.twinklingtree.com/0469176918.jpg","https://cdn.twinklingtree.com/0469197421.jpg",
    "https://cdn.twinklingtree.com/0470937408.mp4","https://cdn.twinklingtree.com/0471431537.mp4",
    "https://cdn.twinklingtree.com/0487263716.mp4","https://cdn.twinklingtree.com/0494948982.jpeg",
    "https://cdn.twinklingtree.com/0498864908.mp4","https://cdn.twinklingtree.com/0506149879.jpg",
    "https://cdn.twinklingtree.com/0516228867.jpg","https://cdn.twinklingtree.com/0518600376.jpg",
    "https://cdn.twinklingtree.com/0522303116.mp4","https://cdn.twinklingtree.com/0522609346.mp4",
    "https://cdn.twinklingtree.com/0525293970.jpg","https://cdn.twinklingtree.com/0537678898.jpg",
    "https://cdn.twinklingtree.com/0539174088.jpg","https://cdn.twinklingtree.com/0540435171.jpg",
    "https://cdn.twinklingtree.com/0548558759.mp4","https://cdn.twinklingtree.com/0552567667.jpg",
    "https://cdn.twinklingtree.com/0560347446.mp4","https://cdn.twinklingtree.com/0562146857.mp4",
    "https://cdn.twinklingtree.com/0563448619.jpg","https://cdn.twinklingtree.com/0570272537.jpg",
    "https://cdn.twinklingtree.com/0571761636.jpg","https://cdn.twinklingtree.com/0572491507.jpg",
    "https://cdn.twinklingtree.com/0574469359.mp4","https://cdn.twinklingtree.com/0575168092.jpg",
    "https://cdn.twinklingtree.com/0575506678.jpg","https://cdn.twinklingtree.com/0576104801.mp4",
    "https://cdn.twinklingtree.com/0580397756.jpg","https://cdn.twinklingtree.com/0582998611.mp4",
    "https://cdn.twinklingtree.com/0583072414.mp4","https://cdn.twinklingtree.com/0591347092.jpg",
    "https://cdn.twinklingtree.com/0591835999.jpg","https://cdn.twinklingtree.com/0593380219.jpg",
    "https://cdn.twinklingtree.com/0593609273.mp4","https://cdn.twinklingtree.com/0600012913.jpg",
    "https://cdn.twinklingtree.com/0601128006.jpg","https://cdn.twinklingtree.com/0601666329.mp4",
    "https://cdn.twinklingtree.com/0604046243.mp4","https://cdn.twinklingtree.com/0604158112.jpg",
    "https://cdn.twinklingtree.com/0606355746.jpg","https://cdn.twinklingtree.com/0608519498.mp4",
    "https://cdn.twinklingtree.com/0614715416.mp4","https://cdn.twinklingtree.com/0623184181.jpg",
    "https://cdn.twinklingtree.com/0624291490.jpg","https://cdn.twinklingtree.com/0641103152.mp4",
    "https://cdn.twinklingtree.com/0642387458.mp4","https://cdn.twinklingtree.com/0643046959.mp4",
    "https://cdn.twinklingtree.com/0643152258.mp4","https://cdn.twinklingtree.com/0643235456.mp4",
    "https://cdn.twinklingtree.com/0650540596.jpg","https://cdn.twinklingtree.com/0655596604.mp4",
    "https://cdn.twinklingtree.com/0665008883.mp4","https://cdn.twinklingtree.com/0671245674.jpg",
    "https://cdn.twinklingtree.com/0676933228.jpg","https://cdn.twinklingtree.com/0686455468.png",
    "https://cdn.twinklingtree.com/0693841532.jpg","https://cdn.twinklingtree.com/0695340650.jpg",
    "https://cdn.twinklingtree.com/0698194760.jpg","https://cdn.twinklingtree.com/0701472469.jpg",
    "https://cdn.twinklingtree.com/0715884672.jpg","https://cdn.twinklingtree.com/0716959959.mp4",
    "https://cdn.twinklingtree.com/0717101690.jpg","https://cdn.twinklingtree.com/0742001840.jpg",
    "https://cdn.twinklingtree.com/0743850167.mp4","https://cdn.twinklingtree.com/0745838447.mp4",
    "https://cdn.twinklingtree.com/0747493036.mp4","https://cdn.twinklingtree.com/0752969586.mp4",
    "https://cdn.twinklingtree.com/0753040482.jpg","https://cdn.twinklingtree.com/0757076923.mp4",
    "https://cdn.twinklingtree.com/0757409391.jpg","https://cdn.twinklingtree.com/0762697366.png",
]

def load_db():
    if MATCHES_DB.exists():
        return json.loads(MATCHES_DB.read_text())
    return {}

def save_db(db):
    MATCHES_DB.write_text(json.dumps(db, indent=2))

def md5_file(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()

def is_video_url(url):
    return "adspyder-videos" in url or url.endswith(".mp4")

def download_file(url, dest):
    if Path(dest).exists() and Path(dest).stat().st_size > 0:
        return True
    try:
        r = req.get(url, timeout=30)
        r.raise_for_status()
        Path(dest).write_bytes(r.content)
        return True
    except:
        return False

def get_image_path(filepath, is_vid):
    if not is_vid:
        return filepath
    frame = filepath + "_frame.jpg"
    if Path(frame).exists() and Path(frame).stat().st_size > 0:
        return frame
    subprocess.run(["ffmpeg", "-i", filepath, "-ss", "1", "-vframes", "1", frame, "-y", "-loglevel", "quiet"],
                   capture_output=True, timeout=30)
    if not Path(frame).exists():
        subprocess.run(["ffmpeg", "-i", filepath, "-vframes", "1", frame, "-y", "-loglevel", "quiet"],
                       capture_output=True, timeout=30)
    return frame if Path(frame).exists() else None

def phash_file(filepath, is_vid=False):
    imgpath = get_image_path(filepath, is_vid)
    if not imgpath or not Path(imgpath).exists():
        return None
    try:
        img = Image.open(imgpath).convert("RGB").resize((256, 256))
        return imagehash.phash(img)
    except:
        return None

def extract_urls_from_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    import re
    urls = re.findall(r'https?://\S+', text)
    return [u.strip('.,)') for u in urls]

def ask_claude_vision(img1_path, img2_path, ads_url, our_url):
    """Ask Claude if two images are the same product."""
    try:
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        imgs = []
        for p in [img1_path, img2_path]:
            if not p or not Path(p).exists():
                return None
            data = Path(p).read_bytes()
            import base64
            # Resize to keep under 5MB
            img = Image.open(p).convert("RGB")
            img.thumbnail((600, 600))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=80)
            imgs.append(base64.standard_b64encode(buf.getvalue()).decode())

        msg = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=50,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": imgs[0]}},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": imgs[1]}},
                    {"type": "text", "text": "Are these two images showing the exact same product? Reply with only YES or NO."}
                ]
            }]
        )
        answer = msg.content[0].text.strip().upper()
        return answer == "YES"
    except Exception as e:
        print(f"Claude error: {e}")
        return None

# Pre-download and hash our library in background
our_hashes = {}
our_md5s = {}
_library_ready = False

def build_library():
    global our_hashes, our_md5s, _library_ready
    for url in OUR_LINKS:
        fname = url.split("/")[-1]
        ext = "." + fname.split(".")[-1]
        dest = CACHE_DIR / ("our_" + fname + ext)
        if not dest.exists():
            download_file(url, str(dest))
        if dest.exists():
            our_md5s[md5_file(str(dest))] = url
            is_vid = dest.suffix == ".mp4"
            h = phash_file(str(dest), is_vid)
            if h:
                our_hashes[url] = h
    _library_ready = True
    print(f"Library ready: {len(our_hashes)} hashed, {len(our_md5s)} MD5s")

threading.Thread(target=build_library, daemon=True).start()

def match_url(ads_url, db):
    """Try to match an AdSpyder URL to one of our links. Returns (our_url, method) or (None, None)."""
    # 1. Check learned DB first
    ads_id = ads_url.split("/")[-1]
    if ads_url in db:
        return db[ads_url], "learned"

    # 2. Download file
    is_vid = is_video_url(ads_url)
    ext = ".mp4" if is_vid else ".jpg"
    dest = CACHE_DIR / ("ads_" + ads_id + ext)
    if not download_file(ads_url, str(dest)):
        return None, None

    # 3. MD5 exact match
    m = md5_file(str(dest))
    if m in our_md5s:
        return our_md5s[m], "exact"

    # 4. Strict phash (d<=3)
    ah = phash_file(str(dest), is_vid)
    if ah:
        best_url, best_dist = None, 999
        for our_url, oh in our_hashes.items():
            d = ah - oh
            if d < best_dist:
                best_dist = d
                best_url = our_url
        if best_dist <= 3:
            return best_url, "hash"

        # 5. Claude vision on top candidate if dist <= 40
        if best_dist <= 40 and CLAUDE_API_KEY and best_url:
            our_fname = best_url.split("/")[-1]
            our_ext = "." + our_fname.split(".")[-1]
            our_dest = CACHE_DIR / ("our_" + our_fname + our_ext)
            our_is_vid = our_dest.suffix == ".mp4"
            ads_img = get_image_path(str(dest), is_vid)
            our_img = get_image_path(str(our_dest), our_is_vid)
            result = ask_claude_vision(ads_img, our_img, ads_url, best_url)
            if result:
                return best_url, "vision"

    return None, None

# Job tracking
jobs = {}

def run_job(job_id, urls):
    db = load_db()
    results = []
    total = len(urls)
    for i, url in enumerate(urls):
        jobs[job_id]["progress"] = i + 1
        jobs[job_id]["current"] = url.split("/")[-1]
        our_url, method = match_url(url, db)
        if our_url:
            db[url] = our_url  # learn it
            save_db(db)
        results.append({"ads": url, "our": our_url or "", "method": method or ""})
    jobs[job_id]["results"] = results
    jobs[job_id]["done"] = True
    jobs[job_id]["total"] = total

# --- HTML Templates ---

LOGIN_HTML = """<!DOCTYPE html>
<html><head><title>AdSpyder Matcher</title>
<style>
* { box-sizing: border-box; } body { font-family: Arial, sans-serif; background: #1a1a2e; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
.box { background: white; padding: 40px; border-radius: 12px; width: 360px; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
h2 { margin-top: 0; color: #333; } input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 15px; margin: 10px 0; }
button { width: 100%; padding: 12px; background: #4CAF50; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; }
button:hover { background: #45a049; } .err { color: red; font-size: 13px; }
</style></head><body>
<div class="box">
  <h2>🔒 AdSpyder Matcher</h2>
  <form method="post">
    <input type="password" name="password" placeholder="Enter password" autofocus>
    <button type="submit">Login</button>
  </form>
  {% if error %}<p class="err">Incorrect password</p>{% endif %}
</div></body></html>"""

MAIN_HTML = """<!DOCTYPE html>
<html><head><title>AdSpyder Matcher</title>
<style>
* { box-sizing: border-box; } body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
.container { max-width: 900px; margin: 0 auto; }
h1 { color: #333; margin-bottom: 4px; } .sub { color: #888; font-size: 14px; margin-bottom: 24px; }
.card { background: white; border-radius: 10px; padding: 28px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 20px; }
.upload-area { border: 2px dashed #ccc; border-radius: 8px; padding: 40px; text-align: center; cursor: pointer; transition: all 0.2s; }
.upload-area:hover, .upload-area.drag { border-color: #4CAF50; background: #f9fff9; }
.upload-area input { display: none; }
.btn { padding: 12px 28px; background: #4CAF50; color: white; border: none; border-radius: 6px; font-size: 15px; cursor: pointer; }
.btn:hover { background: #45a049; } .btn:disabled { background: #aaa; cursor: not-allowed; }
.btn-blue { background: #2196F3; } .btn-blue:hover { background: #1976D2; }
#progress { display: none; } .bar-wrap { background: #eee; border-radius: 20px; height: 12px; margin: 10px 0; }
.bar { background: #4CAF50; height: 12px; border-radius: 20px; transition: width 0.3s; }
#results { display: none; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { background: #333; color: white; padding: 10px; text-align: left; }
td { padding: 8px 10px; border-bottom: 1px solid #eee; word-break: break-all; }
tr:nth-child(even) { background: #fafafa; }
.matched { color: #2e7d32; } .unmatched { color: #aaa; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold; }
.badge-exact { background: #e8f5e9; color: #2e7d32; }
.badge-hash { background: #e3f2fd; color: #1565c0; }
.badge-vision { background: #f3e5f5; color: #6a1b9a; }
.badge-learned { background: #fff8e1; color: #f57f17; }
.stats { display: flex; gap: 16px; margin-bottom: 16px; }
.stat { background: #f5f5f5; border-radius: 8px; padding: 12px 20px; text-align: center; }
.stat-num { font-size: 28px; font-weight: bold; color: #333; }
.stat-label { font-size: 12px; color: #888; }
</style></head><body>
<div class="container">
  <h1>🔍 AdSpyder Link Matcher</h1>
  <p class="sub">Upload a PDF of stolen links — the system will match them to your original content.</p>

  <div class="card">
    <div class="upload-area" id="dropzone" onclick="document.getElementById('pdfFile').click()">
      <input type="file" id="pdfFile" accept=".pdf" onchange="fileSelected(this)">
      <div style="font-size:40px">📄</div>
      <div style="font-size:16px;margin:8px 0;color:#555">Drop PDF here or click to upload</div>
      <div style="font-size:13px;color:#aaa">Accepts AdSpyder stolen links PDF</div>
    </div>
    <div id="fileInfo" style="display:none;margin-top:12px;color:#555;font-size:14px"></div>
    <div style="margin-top:16px">
      <button class="btn" id="startBtn" onclick="startJob()" disabled>Start Matching</button>
    </div>
  </div>

  <div class="card" id="progress">
    <h3 style="margin-top:0">Processing...</h3>
    <div id="progressText" style="font-size:14px;color:#555;margin-bottom:8px">Starting...</div>
    <div class="bar-wrap"><div class="bar" id="bar" style="width:0%"></div></div>
    <div id="progressDetail" style="font-size:12px;color:#aaa;margin-top:6px"></div>
  </div>

  <div class="card" id="results">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
      <h3 style="margin:0">Results</h3>
      <button class="btn btn-blue" onclick="downloadCSV()">⬇ Download CSV</button>
    </div>
    <div class="stats" id="statsArea"></div>
    <table id="resultsTable">
      <thead><tr><th>#</th><th>AdSpyder Link</th><th>Our Link</th><th>Method</th></tr></thead>
      <tbody id="resultsBody"></tbody>
    </table>
  </div>
</div>

<script>
let selectedFile = null;
let currentJobId = null;
let allResults = [];

const dropzone = document.getElementById('dropzone');
dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('drag'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag'));
dropzone.addEventListener('drop', e => {
  e.preventDefault(); dropzone.classList.remove('drag');
  const f = e.dataTransfer.files[0];
  if (f && f.name.endsWith('.pdf')) { selectedFile = f; showFileInfo(f); }
});

function fileSelected(input) {
  selectedFile = input.files[0];
  if (selectedFile) showFileInfo(selectedFile);
}

function showFileInfo(f) {
  document.getElementById('fileInfo').style.display = 'block';
  document.getElementById('fileInfo').textContent = '📎 ' + f.name + ' (' + (f.size/1024).toFixed(0) + ' KB)';
  document.getElementById('startBtn').disabled = false;
}

async function startJob() {
  if (!selectedFile) return;
  document.getElementById('startBtn').disabled = true;
  const fd = new FormData();
  fd.append('pdf', selectedFile);
  const res = await fetch('/upload', { method: 'POST', body: fd });
  const data = await res.json();
  if (data.job_id) {
    currentJobId = data.job_id;
    document.getElementById('progress').style.display = 'block';
    pollProgress();
  } else {
    alert('Error: ' + (data.error || 'Unknown error'));
    document.getElementById('startBtn').disabled = false;
  }
}

async function pollProgress() {
  const res = await fetch('/progress/' + currentJobId);
  const data = await res.json();
  const pct = data.total ? Math.round(data.progress / data.total * 100) : 0;
  document.getElementById('bar').style.width = pct + '%';
  document.getElementById('progressText').textContent = `Processing ${data.progress} / ${data.total} links (${pct}%)`;
  document.getElementById('progressDetail').textContent = data.current ? 'Current: ' + data.current : '';
  if (!data.done) {
    setTimeout(pollProgress, 1500);
  } else {
    showResults(data.results);
  }
}

function showResults(results) {
  allResults = results;
  document.getElementById('progress').style.display = 'none';
  document.getElementById('results').style.display = 'block';
  const matched = results.filter(r => r.our).length;
  document.getElementById('statsArea').innerHTML = `
    <div class="stat"><div class="stat-num">${results.length}</div><div class="stat-label">Total Links</div></div>
    <div class="stat"><div class="stat-num" style="color:#2e7d32">${matched}</div><div class="stat-label">Matched</div></div>
    <div class="stat"><div class="stat-num" style="color:#c62828">${results.length-matched}</div><div class="stat-label">Unmatched</div></div>
  `;
  const tbody = document.getElementById('resultsBody');
  tbody.innerHTML = '';
  results.forEach((r, i) => {
    const badge = r.method ? `<span class="badge badge-${r.method}">${r.method}</span>` : '';
    tbody.innerHTML += `<tr>
      <td>${i+1}</td>
      <td class="${r.our ? 'matched' : 'unmatched'}"><a href="${r.ads}" target="_blank" style="color:inherit">${r.ads}</a></td>
      <td>${r.our ? '<a href="'+r.our+'" target="_blank">'+r.our+'</a>' : '<span style="color:#bbb">—</span>'}</td>
      <td>${badge}</td>
    </tr>`;
  });
}

function downloadCSV() {
  let csv = 'AdSpyder Link,Our Link,Method\\n';
  allResults.forEach(r => { csv += `"${r.ads}","${r.our}","${r.method}"\\n`; });
  const blob = new Blob([csv], {type:'text/csv'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'matched_links.csv';
  a.click();
}
</script>
</body></html>"""

# --- Routes ---

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            session["auth"] = True
            return redirect("/")
        return render_template_string(LOGIN_HTML, error=True)
    if not session.get("auth"):
        return render_template_string(LOGIN_HTML, error=False)
    return render_template_string(MAIN_HTML)

@app.route("/upload", methods=["POST"])
def upload():
    if not session.get("auth"):
        return jsonify({"error": "Unauthorized"}), 401
    f = request.files.get("pdf")
    if not f:
        return jsonify({"error": "No file"}), 400
    urls = extract_urls_from_pdf(f.read())
    if not urls:
        return jsonify({"error": "No URLs found in PDF"}), 400
    job_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
    jobs[job_id] = {"progress": 0, "total": len(urls), "done": False, "current": "", "results": []}
    threading.Thread(target=run_job, args=(job_id, urls), daemon=True).start()
    return jsonify({"job_id": job_id, "total": len(urls)})

@app.route("/progress/<job_id>")
def progress(job_id):
    if not session.get("auth"):
        return jsonify({"error": "Unauthorized"}), 401
    job = jobs.get(job_id, {})
    return jsonify(job)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
