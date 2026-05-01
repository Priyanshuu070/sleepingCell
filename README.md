# 🔔 sleepingCell — Google Form Change Monitor

A Python automation script that monitors a Google Form for changes and sends you instant **email notifications** the moment anything is updated — fields, options, or structure.

***

## 🚀 What It Does

- Navigates through a multi-page Google Form (including login-restricted, org-only forms)
- Scrapes all fields, options, and structure across every page
- Compares the current state against the last saved snapshot
- Sends an **email alert** if anything changes
- Runs automatically **4 times a day** (8am, 12pm, 4pm, 8pm) in the background
- Works silently — no terminal window needed while you work

***

## 🛠️ Tech Stack

- **Python 3.11+**
- **Selenium** — browser automation (attaches to a live Chrome session)
- **BeautifulSoup4** — HTML parsing
- **smtplib** — Gmail email notifications
- **schedule** — task scheduler
- **python-dotenv** — environment variable management

***

## ⚙️ Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/sleepingCell.git
cd sleepingCell
```

### 2. Install Dependencies

```bash
pip install selenium webdriver-manager beautifulsoup4 python-dotenv schedule
```

### 3. Create `.env` File

Create a `.env` file in the project root:

```env
FORM_URL=https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform
SENDER_EMAIL=you@gmail.com
SENDER_PASSWORD=your_gmail_app_password
RECEIVER_EMAIL=you@gmail.com
```

> ⚠️ **Never commit `.env` to GitHub.** It is already in `.gitignore`.

### 4. Gmail App Password

Gmail requires an **App Password** (not your account password) for SMTP:

1. Go to [myaccount.google.com](https://myaccount.google.com) → Security
2. Enable 2-Step Verification if not already on
3. Go to **App Passwords** → create one for "Mail"
4. Paste that 16-character password as `SENDER_PASSWORD` in `.env`

### 5. Fix Email Going to Spam (Important)

Run the monitor once, then:

1. Open Gmail → Spam folder → find the monitor email
2. Click **"Not spam"**
3. Go to **Settings → Filters and Blocked Addresses → Create a new filter**
4. In the **From** field enter your `SENDER_EMAIL`
5. Click **Next** → check **"Never send it to Spam"** + **"Mark as important"**
6. Click **Create filter**

All future alerts will go straight to inbox with a notification.

***

## ▶️ Running the Script

### Step 1: Start Chrome with Remote Debug Port

The form may be login-restricted, so the script attaches to a live authenticated Chrome session. **Double-click `start_chrome_debug.bat`** — this opens Chrome on port 9333.

> First time only: log into your Google account in the Chrome window that opens.

### Step 2: Test Mode — verify scraping works

```bash
python monitor.py --test
```

Prints all scraped fields as JSON. No email sent. No scheduler started.

### Step 3: Normal Mode — run + start scheduler

```bash
python monitor.py
```

Runs an immediate check, saves the baseline snapshot, then schedules checks at **8am, 12pm, 4pm, 8pm** daily.

### Step 4: Silent Background Mode (Windows)

**Double-click `run_monitor.vbs`** — runs the script with no terminal window.

To stop the background process:
```powershell
taskkill /F /IM pythonw.exe
```

***

## 🔁 Auto-Start on Windows Boot

1. Press `Win + R` → type `shell:startup` → Enter
2. Copy both files into the Startup folder:
   - `1_start_chrome_debug.bat`
   - `2_run_monitor.vbs`

Rename with `1_` and `2_` prefixes — Windows runs startup items alphabetically, ensuring Chrome is ready before the monitor connects.

***

## 📁 Project Structure

```
sleepingCell/
├── monitor.py              # Main script
├── start_chrome_debug.bat  # Launches Chrome with remote debug port
├── run_monitor.vbs         # Silent background launcher
├── last_state.json         # Auto-generated: stores previous form snapshot
├── .env                    # Secrets (not committed)
├── .gitignore
└── README.md
```

***

## 📬 Email Notification Example

```
Subject: Form Alert: Form Updated

Hi,

The monitored form has been updated. Here's a summary of changes:

➕ NEW QUESTION: Resume submission deadline
   Options: Yes, No

✏️ CHANGED OPTIONS in: Are you interested?
   Added options: Maybe

Form Link: https://docs.google.com/forms/...
Detected at: 01 May 2026, 04:00 PM
```

***

## ⚠️ Important Notes

| Topic | Note |
|-------|------|
| Chrome must be open | The monitor attaches to Chrome via port 9333 — Chrome must be running |
| Keep this Chrome instance dedicated | Avoid using it for regular browsing |
| PC must be on at check times | The scheduler cannot wake a sleeping PC |
| Form is never submitted | The script navigates pages with dummy data but stops before Submit |

***

## 🔧 Troubleshooting

**`SessionNotCreatedException: cannot connect to chrome at 127.0.0.1:9333`**
→ Chrome isn't running on the debug port. Double-click `start_chrome_debug.bat` first.

**`Expecting value: line 1 column 1`**
→ `last_state.json` is empty or corrupt. Delete it and re-run.

**Email going to spam**
→ Follow the Gmail filter setup in Step 5 of the Setup section above.

**Fields not being scraped on a page**
→ Run `python monitor.py --test` to verify. Some form pages are info-only and intentionally return 0 fields.

***

## 📄 License

MIT License — use freely, modify as needed.