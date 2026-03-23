"""
RCB Ticket Monitor - Render Web Service
Monitors ticket availability and sends alerts via email
"""

import requests
from bs4 import BeautifulSoup
import time
import threading
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# ─── CONFIG (set these as Environment Variables in Render) ───────────────────
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "")           # Your email to receive alerts
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "")             # Gmail you'll send FROM
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")       # Gmail App Password
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "60"))  # seconds
# ─────────────────────────────────────────────────────────────────────────────

AVAILABLE_KEYWORDS = [
    "book now", "buy tickets", "book tickets",
    "tickets available", "get tickets", "select seats",
    "add to cart", "buy now"
]

UNAVAILABLE_KEYWORDS = [
    "sold out", "notify me", "coming soon",
    "not available", "no tickets"
]

MONITOR_URLS = [
    {
        "name": "BookMyShow - RCB vs SRH",
        "url": "https://in.bookmyshow.com/sports/royal-challengers-bengaluru-vs-sunrisers-hyderabad/ET00415951",
    },
    {
        "name": "RCB Official - Tickets",
        "url": "https://www.royalchallengers.com/tickets",
    },
    {
        "name": "District (Zomato) - RCB Tickets",
        "url": "https://www.district.in/royal-challengers-bengaluru-vs-sunrisers-hyderabad-mar28-2025-evr/event",
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

# ─── Shared State ─────────────────────────────────────────────────────────────
monitor_state = {
    "running": True,
    "check_count": 0,
    "last_checked": None,
    "alerts_sent": 0,
    "sites": [{"name": s["name"], "url": s["url"], "status": "⏳ Checking...", "available": False} for s in MONITOR_URLS],
    "log": []
}


def log(msg):
    timestamp = datetime.now().strftime("%d %b %Y, %I:%M:%S %p")
    entry = f"[{timestamp}] {msg}"
    print(entry)
    monitor_state["log"].insert(0, entry)
    if len(monitor_state["log"]) > 100:
        monitor_state["log"].pop()


def send_email_alert(site_name, url):
    if not ALERT_EMAIL or not SMTP_EMAIL or not SMTP_PASSWORD:
        log("⚠️ Email not configured — skipping email alert")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🔴 RCB TICKETS ARE LIVE! Book NOW!"
        msg["From"] = SMTP_EMAIL
        msg["To"] = ALERT_EMAIL

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px;background:#1a1a2e;color:white;border-radius:12px;">
            <h1 style="color:#FF3B3B;text-align:center;">🏏 RCB TICKETS ARE LIVE!</h1>
            <p style="font-size:18px;text-align:center;">Tickets detected on <strong>{site_name}</strong></p>
            <div style="text-align:center;margin:30px 0;">
                <a href="{url}" style="background:#FF3B3B;color:white;padding:16px 32px;border-radius:8px;text-decoration:none;font-size:20px;font-weight:bold;">
                    👉 BOOK NOW
                </a>
            </div>
            <p style="color:#aaa;text-align:center;font-size:12px;">RCB vs SRH · March 28 · M. Chinnaswamy Stadium, Bangalore</p>
            <p style="color:#aaa;text-align:center;font-size:12px;">Detected at: {datetime.now().strftime("%d %b %Y, %I:%M:%S %p")}</p>
        </div>
        """

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, ALERT_EMAIL, msg.as_string())

        log(f"✅ Email alert sent to {ALERT_EMAIL}")
        monitor_state["alerts_sent"] += 1

    except Exception as e:
        log(f"❌ Email failed: {e}")


def check_url(site):
    try:
        resp = requests.get(site["url"], headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        page_text = soup.get_text(separator=" ").lower()

        found_available = [kw for kw in AVAILABLE_KEYWORDS if kw in page_text]
        found_unavailable = [kw for kw in UNAVAILABLE_KEYWORDS if kw in page_text]

        if found_available and not found_unavailable:
            return True, f"Found: {found_available}"
        return False, "Not available yet"

    except Exception as e:
        return False, f"Error: {str(e)[:60]}"


def monitor_loop():
    log("🚀 Monitoring started!")
    while monitor_state["running"]:
        monitor_state["check_count"] += 1
        monitor_state["last_checked"] = datetime.now().strftime("%d %b %Y, %I:%M:%S %p")
        log(f"🔍 Check #{monitor_state['check_count']} started")

        for i, site in enumerate(MONITOR_URLS):
            available, reason = check_url(site)
            monitor_state["sites"][i]["available"] = available
            monitor_state["sites"][i]["status"] = "✅ TICKETS LIVE!" if available else f"⏳ {reason}"

            if available:
                log(f"🚨 TICKETS LIVE on {site['name']}! Sending alert...")
                send_email_alert(site["name"], site["url"])
            else:
                log(f"  {site['name']}: {reason}")

        time.sleep(CHECK_INTERVAL)


# ─── Dashboard HTML ───────────────────────────────────────────────────────────
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>RCB Ticket Monitor</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #0d0d1a; color: #f0f0f0; font-family: 'Segoe UI', sans-serif; padding: 20px; }
    .header { text-align: center; padding: 30px 0 20px; }
    .header h1 { font-size: 2rem; color: #FF3B3B; }
    .header p { color: #aaa; margin-top: 6px; }
    .stats { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; margin: 20px 0; }
    .stat-card { background: #1a1a2e; border-radius: 12px; padding: 16px 24px; text-align: center; min-width: 140px; }
    .stat-card .num { font-size: 2rem; font-weight: bold; color: #FF3B3B; }
    .stat-card .label { font-size: 0.8rem; color: #888; margin-top: 4px; }
    .sites { display: grid; gap: 12px; max-width: 700px; margin: 0 auto 24px; }
    .site-card { background: #1a1a2e; border-radius: 12px; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; border: 2px solid transparent; }
    .site-card.live { border-color: #00ff88; background: #0a2a1a; animation: pulse 1s infinite; }
    @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.85; } }
    .site-name { font-weight: bold; font-size: 0.95rem; }
    .site-url { font-size: 0.75rem; color: #666; margin-top: 3px; }
    .site-status { font-size: 0.9rem; }
    .log-box { max-width: 700px; margin: 0 auto; background: #111; border-radius: 12px; padding: 16px; max-height: 300px; overflow-y: auto; }
    .log-box h3 { color: #FF3B3B; margin-bottom: 10px; font-size: 0.9rem; }
    .log-entry { font-size: 0.78rem; color: #aaa; padding: 3px 0; border-bottom: 1px solid #1a1a1a; }
    .refresh-note { text-align: center; color: #555; font-size: 0.75rem; margin-top: 16px; }
    a { color: #FF3B3B; }
  </style>
  <meta http-equiv="refresh" content="15">
</head>
<body>
  <div class="header">
    <h1>🏏 RCB Ticket Monitor</h1>
    <p>RCB vs SRH · March 28 · M. Chinnaswamy Stadium, Bangalore</p>
  </div>

  <div class="stats">
    <div class="stat-card">
      <div class="num">{{ state.check_count }}</div>
      <div class="label">Checks Done</div>
    </div>
    <div class="stat-card">
      <div class="num">{{ state.alerts_sent }}</div>
      <div class="label">Alerts Sent</div>
    </div>
    <div class="stat-card">
      <div class="num">{{ state.sites | selectattr('available') | list | length }}</div>
      <div class="label">Sites Live</div>
    </div>
  </div>

  <div class="sites">
    {% for site in state.sites %}
    <div class="site-card {% if site.available %}live{% endif %}">
      <div>
        <div class="site-name">{{ site.name }}</div>
        <div class="site-url"><a href="{{ site.url }}" target="_blank">{{ site.url[:55] }}...</a></div>
      </div>
      <div class="site-status">{{ site.status }}</div>
    </div>
    {% endfor %}
  </div>

  <div class="log-box">
    <h3>📋 Activity Log</h3>
    {% for entry in state.log %}
    <div class="log-entry">{{ entry }}</div>
    {% endfor %}
  </div>

  <div class="refresh-note">Last checked: {{ state.last_checked or 'Starting...' }} · Page auto-refreshes every 15s</div>
</body>
</html>
"""


@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD_HTML, state=monitor_state)


@app.route("/status")
def status():
    return jsonify(monitor_state)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "checks": monitor_state["check_count"]})


if __name__ == "__main__":
    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
