# 🏏 RCB Ticket Monitor — Render Deployment

Monitors BookMyShow, RCB Official & District (Zomato) every 60 seconds.
Sends an **email alert** the moment tickets go live!

---

## 📁 Files
- `app.py` — Flask web app + background monitor thread
- `requirements.txt` — Python dependencies
- `render.yaml` — Render deployment config

---

## 🚀 Deploy to Render (Step by Step)

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "RCB ticket monitor"
git remote add origin https://github.com/YOUR_USERNAME/rcb-monitor.git
git push -u origin main
```

### Step 2 — Create Render Web Service
1. Go to https://render.com and sign up (free)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` — click **Deploy**

### Step 3 — Set Environment Variables in Render Dashboard
| Key | Value |
|-----|-------|
| `ALERT_EMAIL` | Your email to receive alerts |
| `SMTP_EMAIL` | Your Gmail address |
| `SMTP_PASSWORD` | Gmail App Password (see below) |
| `CHECK_INTERVAL` | `60` (seconds between checks) |

### Step 4 — Get Gmail App Password
1. Go to myaccount.google.com → Security
2. Enable **2-Step Verification**
3. Search "App passwords" → Generate one for "Mail"
4. Use that 16-character password as `SMTP_PASSWORD`

---

## 📊 Dashboard
Once deployed, visit your Render URL (e.g. `https://rcb-monitor.onrender.com`) to see:
- Live status of all monitored sites
- Check count and alerts sent
- Activity log

---

## ⚠️ Free Tier Note
Render free tier **spins down after 15 mins of inactivity**.
To keep it always alive, use a free uptime service like:
- https://uptimerobot.com — add your Render URL, ping every 5 mins (free)
