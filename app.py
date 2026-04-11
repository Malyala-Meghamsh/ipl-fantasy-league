"""
IPL Fantasy Pipeline – Web Controller
Run this Flask app, then open from your phone to trigger
the scraping pipeline and enter OTP remotely.
"""

import threading
import queue
import time
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# ── Shared state ────────────────────────────────────────────────
pipeline_state = {
    "running": False,
    "stage": "idle",       # idle | waiting_otp | scraping | processing | done | error
    "message": "",
    "logs": [],
}
otp_queue = queue.Queue()


def _add_log(msg):
    pipeline_state["logs"].append({"time": time.strftime("%H:%M:%S"), "msg": msg})


# ── Pipeline runner (background thread) ────────────────────────
def _run_pipeline_thread():
    try:
        pipeline_state["running"] = True
        pipeline_state["stage"] = "scraping"
        pipeline_state["message"] = "Starting pipeline..."
        pipeline_state["logs"] = []
        _add_log("Pipeline started")

        def otp_provider():
            pipeline_state["stage"] = "waiting_otp"
            pipeline_state["message"] = "Enter OTP on your phone"
            _add_log("Waiting for OTP...")
            otp = otp_queue.get()          # blocks until OTP is submitted
            pipeline_state["stage"] = "scraping"
            pipeline_state["message"] = "OTP received, processing..."
            _add_log(f"OTP received")
            return otp

        from daily_ipl_fantasy import run_pipeline
        run_pipeline(otp_provider=otp_provider, log_callback=_add_log)

        pipeline_state["stage"] = "done"
        pipeline_state["message"] = "Pipeline completed successfully!"
        _add_log("Pipeline completed ✅")
    except Exception as e:
        pipeline_state["stage"] = "error"
        pipeline_state["message"] = f"Error: {e}"
        _add_log(f"Error: {e}")
    finally:
        pipeline_state["running"] = False


# ── API Routes ──────────────────────────────────────────────────
@app.route("/api/start", methods=["POST"])
def api_start():
    if pipeline_state["running"]:
        return jsonify({"ok": False, "error": "Pipeline already running"}), 409
    # Drain any old OTP
    while not otp_queue.empty():
        otp_queue.get_nowait()
    t = threading.Thread(target=_run_pipeline_thread, daemon=True)
    t.start()
    return jsonify({"ok": True})


@app.route("/api/otp", methods=["POST"])
def api_otp():
    data = request.get_json(force=True)
    otp = data.get("otp", "").strip()
    if not otp:
        return jsonify({"ok": False, "error": "OTP is required"}), 400
    if len(otp) < 4 or len(otp) > 8 or not otp.isdigit():
        return jsonify({"ok": False, "error": "OTP must be 4-8 digits"}), 400
    otp_queue.put(otp)
    return jsonify({"ok": True})


@app.route("/api/status")
def api_status():
    return jsonify({
        "running": pipeline_state["running"],
        "stage": pipeline_state["stage"],
        "message": pipeline_state["message"],
        "logs": pipeline_state["logs"][-30:],   # last 30 entries
    })


# ── Main page ───────────────────────────────────────────────────
DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>IPL Fantasy Controller</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0a0a1a; color: #e0e0e0; min-height:100vh;
    display:flex; flex-direction:column; align-items:center;
    padding: 20px 16px;
  }
  .container { max-width:420px; width:100%; }
  h1 {
    text-align:center; font-size:1.5em; margin-bottom:8px;
    background: linear-gradient(135deg, #f7971e, #ffd200);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text;
  }
  .subtitle { text-align:center; color:#888; font-size:.82em; margin-bottom:24px; }

  /* Status badge */
  .status-bar {
    display:flex; align-items:center; gap:10px;
    padding:14px 16px; border-radius:12px;
    background:#111125; margin-bottom:16px;
  }
  .status-dot {
    width:12px; height:12px; border-radius:50%; flex-shrink:0;
  }
  .dot-idle     { background:#555; }
  .dot-running  { background:#ffd200; animation:pulse 1s infinite; }
  .dot-otp      { background:#ff6b6b; animation:pulse .6s infinite; }
  .dot-done     { background:#4caf50; }
  .dot-error    { background:#f44336; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.3} }
  .status-text { font-size:.9em; }

  /* Buttons */
  .btn {
    display:block; width:100%; padding:14px; border:none; border-radius:12px;
    font-size:1em; font-weight:600; cursor:pointer; margin-bottom:12px;
    transition: transform .15s, box-shadow .15s;
  }
  .btn:active { transform:scale(.97); }
  .btn-primary {
    background: linear-gradient(135deg, #f7971e, #ffd200);
    color:#0a0a1a;
  }
  .btn-primary:disabled { opacity:.4; cursor:not-allowed; }
  .btn-danger {
    background: #ff4444; color:#fff;
  }

  /* OTP section */
  .otp-section {
    display:none; background:#111125; border-radius:12px;
    padding:20px; margin-bottom:16px; text-align:center;
    border:2px solid #ff6b6b; animation: glow 1.5s infinite alternate;
  }
  @keyframes glow {
    from { border-color: #ff6b6b; box-shadow: 0 0 8px rgba(255,107,107,.3); }
    to   { border-color: #ffd200; box-shadow: 0 0 16px rgba(255,210,0,.4); }
  }
  .otp-section.active { display:block; }
  .otp-label { font-size:1em; margin-bottom:12px; color:#ffd200; font-weight:600; }
  .otp-input {
    width:100%; padding:16px; font-size:1.8em; text-align:center;
    letter-spacing:.4em; border:2px solid #333; border-radius:10px;
    background:#0a0a1a; color:#fff; outline:none;
    font-family: 'Courier New', monospace;
  }
  .otp-input:focus { border-color:#ffd200; }
  .otp-submit {
    margin-top:12px; padding:12px; width:100%;
    background:#4caf50; color:#fff; border:none; border-radius:10px;
    font-size:1em; font-weight:600; cursor:pointer;
  }
  .otp-submit:disabled { opacity:.4; }

  /* Logs */
  .log-box {
    background:#0d0d20; border-radius:12px; padding:12px;
    max-height:280px; overflow-y:auto; font-size:.78em;
    font-family:'Courier New',monospace; margin-top:12px;
  }
  .log-line { padding:3px 0; border-bottom:1px solid #1a1a30; }
  .log-time { color:#666; margin-right:6px; }
  .log-msg  { color:#ccc; }

  /* Leaderboard link */
  .link-bar {
    text-align:center; margin-top:16px;
  }
  .link-bar a {
    color:#ffd200; text-decoration:none; font-size:.9em;
  }
</style>
</head>
<body>
<div class="container">
  <h1>IPL Fantasy Controller</h1>
  <p class="subtitle">Run pipeline &amp; enter OTP from your phone</p>

  <!-- Status -->
  <div class="status-bar">
    <div class="status-dot dot-idle" id="statusDot"></div>
    <div class="status-text" id="statusText">Idle</div>
  </div>

  <!-- Start button -->
  <button class="btn btn-primary" id="startBtn" onclick="startPipeline()">
    &#9654;  Run Pipeline
  </button>

  <!-- OTP Section -->
  <div class="otp-section" id="otpSection">
    <div class="otp-label">Enter OTP received on your phone</div>
    <input class="otp-input" id="otpInput" type="tel" maxlength="8"
           inputmode="numeric" pattern="[0-9]*" placeholder="------"
           autocomplete="one-time-code">
    <button class="otp-submit" id="otpSubmit" onclick="submitOtp()">
      Submit OTP
    </button>
  </div>

  <!-- Logs -->
  <div class="log-box" id="logBox"></div>

  <div class="link-bar">
    <a href="/leaderboard" target="_blank">View Leaderboard &#8594;</a>
  </div>
</div>

<script>
let polling = null;

function startPipeline() {
  document.getElementById('startBtn').disabled = true;
  fetch('/api/start', {method:'POST'})
    .then(r => r.json())
    .then(d => {
      if (!d.ok) { alert(d.error); document.getElementById('startBtn').disabled = false; return; }
      startPolling();
    });
}

function submitOtp() {
  const otp = document.getElementById('otpInput').value.trim();
  if (!otp || otp.length < 4) { alert('Enter a valid OTP'); return; }
  document.getElementById('otpSubmit').disabled = true;
  fetch('/api/otp', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({otp})})
    .then(r => r.json())
    .then(d => {
      if (!d.ok) alert(d.error);
      else document.getElementById('otpSection').classList.remove('active');
      document.getElementById('otpSubmit').disabled = false;
      document.getElementById('otpInput').value = '';
    });
}

function startPolling() {
  if (polling) return;
  polling = setInterval(pollStatus, 1500);
  pollStatus();
}

function pollStatus() {
  fetch('/api/status').then(r => r.json()).then(s => {
    const dot = document.getElementById('statusDot');
    const txt = document.getElementById('statusText');
    const otp = document.getElementById('otpSection');
    const btn = document.getElementById('startBtn');

    // Status dot
    dot.className = 'status-dot';
    if (s.stage === 'idle')          { dot.classList.add('dot-idle'); }
    else if (s.stage === 'waiting_otp') { dot.classList.add('dot-otp'); }
    else if (s.stage === 'done')     { dot.classList.add('dot-done'); }
    else if (s.stage === 'error')    { dot.classList.add('dot-error'); }
    else                             { dot.classList.add('dot-running'); }

    txt.textContent = s.message || s.stage;

    // OTP section
    if (s.stage === 'waiting_otp') {
      otp.classList.add('active');
      document.getElementById('otpInput').focus();
    } else {
      otp.classList.remove('active');
    }

    // Re-enable button when done
    if (!s.running) {
      btn.disabled = false;
      if (s.stage === 'done' || s.stage === 'error' || s.stage === 'idle') {
        clearInterval(polling);
        polling = null;
      }
    }

    // Logs
    const box = document.getElementById('logBox');
    box.innerHTML = s.logs.map(l =>
      `<div class="log-line"><span class="log-time">${l.time}</span><span class="log-msg">${l.msg}</span></div>`
    ).join('');
    box.scrollTop = box.scrollHeight;
  });
}

// Auto-submit OTP on 6 digits
document.getElementById('otpInput').addEventListener('input', function() {
  if (this.value.length >= 6) submitOtp();
});

// Check status on load
pollStatus();
</script>
</body>
</html>
"""


@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD_HTML)


@app.route("/leaderboard")
def leaderboard():
    import os
    html_path = os.path.join(os.path.dirname(__file__), "docs", "index.html")
    if os.path.isfile(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Leaderboard not generated yet. Run the pipeline first.", 404


if __name__ == "__main__":
    # Accessible from any device on the same network
    app.run(host="0.0.0.0", port=5000, debug=False)
