import os
import json
import hashlib
import smtplib
import schedule
import time
import argparse
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


load_dotenv()

FORM_URL       = os.getenv("FORM_URL")
SENDER_EMAIL   = os.getenv("SENDER_EMAIL")
SENDER_PASS    = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
STATE_FILE     = "last_state.json"

# ── Folders to skip during profile copy (all locked by Brave) ──────────
SKIP_FOLDERS = {
    "Cache", "Cache_Data", "GPUCache", "GrShaderCache",
    "ShaderCache", "DawnGraphiteCache", "DawnWebGPUCache",
    "Code Cache", "Sessions", "Safe Browsing Network"
}

def ignore_locked(src, names):
    """Tell shutil.copytree to skip locked/cache folders."""
    return [n for n in names if n in SKIP_FOLDERS]


# ── 1. Fetch form using Brave + copied profile ─────────────────────────

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import re

def fill_current_page(driver):
    time.sleep(1)

    def js_click(el):
        driver.execute_script("arguments[0].click();", el)

    # ── Email consent checkbox (MUST be first) ─────────────────────────
    try:
        all_checkboxes = driver.find_elements(By.CSS_SELECTOR, "div[role='checkbox']")
        for cb in all_checkboxes:
            if cb.is_displayed() and cb.get_attribute("aria-checked") == "false":
                driver.execute_script("arguments[0].scrollIntoView(true);", cb)
                time.sleep(0.2)
                js_click(cb)
                time.sleep(0.3)
    except:
        pass

    # ── Short text / Email / URL / Phone ──────────────────────────────
    text_inputs = driver.find_elements(
        By.CSS_SELECTOR,
        "input[type='text'], input[type='email'], input[type='url'], input[type='tel']"
    )
    for inp in text_inputs:
        try:
            if not inp.is_displayed() or not inp.is_enabled():
                continue
            if inp.get_attribute("value") != "":
                continue

            placeholder = (inp.get_attribute("placeholder") or "").lower()
            aria_label  = (inp.get_attribute("aria-label") or "").lower()
            input_type  = (inp.get_attribute("type") or "").lower()

            try:
                label_el   = inp.find_element(By.XPATH, "./ancestor::div[@role='listitem'][1]//span[@dir='auto'][1]")
                label_text = label_el.text.lower()
            except:
                label_text = ""

            hint = placeholder + aria_label + label_text

            js_click(inp)
            inp.clear()

            if input_type == "tel" or any(w in hint for w in ["phone", "mobile", "contact", "number", "whatsapp", "enrollment", "roll"]):
                inp.send_keys("9999999999")
            elif input_type == "email" or "email" in hint:
                inp.send_keys("test@test.com")
            else:
                inp.send_keys("Test")
        except:
            pass

    # ── Number inputs ──────────────────────────────────────────────────
    for inp in driver.find_elements(By.CSS_SELECTOR, "input[type='number']"):
        try:
            if inp.is_displayed() and inp.is_enabled() and inp.get_attribute("value") == "":
                js_click(inp)
                inp.send_keys("1")
        except:
            pass

    # ── Paragraph / Long text ──────────────────────────────────────────
    for ta in driver.find_elements(By.CSS_SELECTOR, "textarea"):
        try:
            if ta.is_displayed() and ta.is_enabled():
                js_click(ta)
                ta.send_keys("Test response")
        except:
            pass

    # ── Radio buttons / MCQ (first option per group) ───────────────────
    radio_groups_done = set()
    for radio in driver.find_elements(By.CSS_SELECTOR, "div[role='radio']"):
        try:
            if not radio.is_displayed():
                continue
            parent = radio.find_element(By.XPATH, "./ancestor::div[@role='radiogroup'][1]")
            parent_id = parent.get_attribute("data-params") or parent.id
            if parent_id not in radio_groups_done:
                js_click(radio)
                radio_groups_done.add(parent_id)
        except:
            pass

    # ── Custom Google Forms dropdowns ──────────────────────────────────
    for dd in driver.find_elements(By.CSS_SELECTOR, "div[role='listbox']"):
        try:
            if dd.is_displayed():
                js_click(dd)
                time.sleep(0.5)
                for opt in driver.find_elements(By.CSS_SELECTOR, "div[role='option']"):
                    if opt.is_displayed() and opt.text.strip() not in ("", "Choose"):
                        js_click(opt)
                        time.sleep(0.3)
                        break
        except:
            pass

    # ── Native <select> dropdowns ──────────────────────────────────────
    for sel in driver.find_elements(By.CSS_SELECTOR, "select"):
        try:
            if sel.is_displayed():
                s = Select(sel)
                for opt in s.options:
                    if opt.get_attribute("value") not in ("", "__other_option__"):
                        s.select_by_value(opt.get_attribute("value"))
                        break
        except:
            pass

    # ── Linear scale / Rating (middle option) ─────────────────────────
    scale_groups_done = set()
    for label in driver.find_elements(By.CSS_SELECTOR, "div[role='radiogroup'] label"):
        try:
            if not label.is_displayed():
                continue
            parent = label.find_element(By.XPATH, "./ancestor::div[@role='radiogroup'][1]")
            parent_id = parent.id
            if parent_id not in scale_groups_done:
                all_labels = parent.find_elements(By.CSS_SELECTOR, "label")
                js_click(all_labels[len(all_labels) // 2])
                scale_groups_done.add(parent_id)
        except:
            pass

    # ── Date inputs ────────────────────────────────────────────────────
    for inp in driver.find_elements(By.CSS_SELECTOR, "input[type='date']"):
        try:
            if inp.is_displayed() and inp.is_enabled():
                js_click(inp)
                inp.send_keys("01012000")
        except:
            pass

    # ── Time inputs ────────────────────────────────────────────────────
    for inp in driver.find_elements(By.CSS_SELECTOR, "input[type='time']"):
        try:
            if inp.is_displayed() and inp.is_enabled():
                js_click(inp)
                inp.send_keys("1200PM")
        except:
            pass

    # ── File upload — intentionally skipped ───────────────────────────
    # We only read form structure, never submit. File fields are captured
    # by scrape_current_page() but not filled here.

    time.sleep(1)


def fetch_form_fields(url: str) -> dict:
    options = webdriver.ChromeOptions()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9333")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    def scrape_current_page() -> dict:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        fields = {}
        # ... rest unchanged
        for block in soup.find_all("div", role="listitem"):

            # Try multiple selectors in order of specificity
            title_el = None

            # 1. Google Forms standard question title class
            for span in block.find_all("span"):
                classes = span.get("class", [])
                if any("M7eMe" in c for c in classes):
                    title_el = span
                    break

            # 2. Freebird title div
            if not title_el:
                title_el = block.find("div", class_=lambda c: c and "Title" in " ".join(c if isinstance(c, list) else [c]))

            # 3. Any span with dir=auto that has meaningful text
            if not title_el:
                for span in block.find_all("span", attrs={"dir": "auto"}):
                    text = span.get_text(strip=True)
                    if text and len(text) > 2 and not text.startswith("*"):
                        title_el = span
                        break

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            if not title or title.startswith("*") or len(title) < 2:
                continue

            # Options: all span[dir=auto] text that isn't the title
            all_spans = block.find_all("span", {"dir": "auto"})
            radio_options = [
                s.get_text(strip=True) for s in all_spans
                if s.get_text(strip=True) and s.get_text(strip=True) != title
            ]

            dropdown_options = [
                el.get_text(strip=True)
                for el in block.find_all("div", role="option")
                if el.get_text(strip=True)
            ]

            is_file_upload = bool(
                block.find("input", {"type": "file"}) or
                ("Upload" in block.get_text() and "PDF" in block.get_text())
            )
            is_text_input = bool(
                block.find("input", {"type": "text"}) or
                block.find("textarea") or
                block.find("input", {"type": "tel"}) or
                block.find("input", {"type": "number"})
            )

            all_options = sorted(set(dropdown_options or radio_options))

            if is_file_upload:
                field_type = "file_upload"
            elif is_text_input:
                field_type = "text"
            elif all_options:
                field_type = "choice"
            else:
                field_type = "unknown"

            fields[title] = {"type": field_type, "options": all_options}

        return fields

    def click_next() -> bool:
        try:
            next_btn = driver.find_element(
                By.XPATH,
                '//span[text()="Next"]/ancestor::div[@role="button"] | '
                '//div[@role="button" and @aria-label="Next"]'
            )
            print(f"    Next button found, clicking...")
            driver.execute_script("arguments[0].click();", next_btn)  # JS click
            return True
        except:
            # ... rest unchanged
            errors = driver.find_elements(
                By.XPATH,
                '//*[contains(text(), "required") or contains(text(), "Correct") or contains(text(), "between")]'
            )
            if errors:
                print(f"    Validation errors still present:")
                for err in errors[:5]:
                    try:
                        q = err.find_element(
                            By.XPATH,
                            "./ancestor::div[@role='listitem'][1]//span[@dir='auto'][1]"
                        )
                        print(f"      - Field '{q.text}': {err.text}")
                    except:
                        print(f"      - {err.text}")
            else:
                print(f"    No Next button found (no validation errors either)")
            return False

    try:                                        # ← try is here
        driver.get(url)
        WebDriverWait(driver, 30).until(
            lambda d: d.title != "" and d.title != "New Tab"
        )
        time.sleep(5)  # page 1 needs extra time — has consent checkbox + JS
        print(f"  Page loaded: '{driver.title}'")

        all_fields = {}
        page_num = 1
        prev_source = ""

        while True:
            print(f"  Scraping page {page_num}...")
            time.sleep(3)

            page_fields = scrape_current_page()
            all_fields.update(page_fields)
            print(f"    Found {len(page_fields)} field(s): {list(page_fields.keys())}")

            print(f"    Filling fields with dummy data...")
            fill_current_page(driver)
            time.sleep(1)

            if click_next():
                # Wait for current page content to be replaced
                try:
                    # Grab any element from current page
                    old_element = driver.find_element(By.CSS_SELECTOR, "div[role='listitem']")
                    WebDriverWait(driver, 10).until(
                        EC.staleness_of(old_element)
                    )
                except:
                    pass
                time.sleep(3)  # buffer for new page JS render
                prev_source = driver.page_source
                page_num += 1

            else:
                print(f"  Last page — scraping final fields...")
                final_fields = scrape_current_page()
                all_fields.update(final_fields)
                print(f"    Found {len(final_fields)} field(s): {list(final_fields.keys())}")
                break

        # ← OUTSIDE the while loop, INSIDE the try block
        driver.get(url)
        print(f"\n  Total fields across all pages: {len(all_fields)}")
        return all_fields

    finally:                                    # ← matches the try above
        pass

# ── 2. Hash ────────────────────────────────────────────────────────────

def hash_state(fields: dict) -> str:
    return hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()


# ── 3. Load / Save State ───────────────────────────────────────────────

def load_previous_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(fields: dict):
    with open(STATE_FILE, "w") as f:
        json.dump({
            "hash": hash_state(fields),
            "fields": fields,
            "updated_at": str(datetime.now())
        }, f, indent=2)


# ── 4. Diff ────────────────────────────────────────────────────────────

def compute_diff(old: dict, new: dict) -> str:
    lines = []
    for q in set(new) - set(old):
        lines.append(f"NEW QUESTION: {q}")
        if new[q]["options"]:
            lines.append(f"  Options: {', '.join(new[q]['options'])}")
    for q in set(old) - set(new):
        lines.append(f"REMOVED QUESTION: {q}")
    for q in set(old) & set(new):
        added   = set(new[q].get("options", [])) - set(old[q].get("options", []))
        removed = set(old[q].get("options", [])) - set(new[q].get("options", []))
        if added or removed:
            lines.append(f"CHANGED: {q}")
            if added:   lines.append(f"  + Added options:   {', '.join(added)}")
            if removed: lines.append(f"  - Removed options: {', '.join(removed)}")
    return "\n".join(lines)

def load_previous_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, ValueError):
        print(f"[WARN] last_state.json was corrupt — resetting.")
        return {}
# ── 5. Email ───────────────────────────────────────────────────────────

def send_email(diff_text: str, new_fields: dict):
    subject = "Form Alert: Namankan Form Updated"

    body = f"""Hi Priyanshu,

CDC is sleeping but you are not. Fill the namankan Form ASAP.

The placement form has been updated. Fill it before the deadline!

CHANGES DETECTED:
{diff_text}

Form Link: {FORM_URL}
Detected at: {datetime.now().strftime("%d %B %Y, %I:%M %p")}

-- 
Form Monitor (your script)
"""
    msg = MIMEMultipart()
    msg["From"]     = f"Form Monitor <{SENDER_EMAIL}>"
    msg["To"]       = RECEIVER_EMAIL
    msg["Subject"]  = subject
    msg["Reply-To"] = SENDER_EMAIL
    # This header strongly signals "not spam"
    msg["X-Priority"] = "1"
    msg["Importance"] = "High"
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    print(f"[{datetime.now()}] Email sent.")

# ── 6. Main check ──────────────────────────────────────────────────────

def check_form():
    print(f"[{datetime.now()}] Checking form...")
    try:
        current_fields = fetch_form_fields(FORM_URL)

        if not current_fields:
            print(f"[{datetime.now()}] WARNING: No fields parsed. Check form URL or login.")
            return

        prev_data   = load_previous_state()
        prev_hash   = prev_data.get("hash", "")
        prev_fields = prev_data.get("fields", {})

        if hash_state(current_fields) != prev_hash:
            print(f"[{datetime.now()}] Change detected!")
            diff = compute_diff(prev_fields, current_fields)
            send_email(diff or "Structure changed.", current_fields)
            save_state(current_fields)
        else:
            print(f"[{datetime.now()}] No changes.")

    except Exception as e:
        print(f"[{datetime.now()}] ERROR: {e}")


# ── 7. Entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a single check and print fields. No scheduler, no email."
    )
    args = parser.parse_args()

    if args.test:
        # ── TEST MODE: just print fields, no email, no scheduler ──
        print("=== TEST MODE ===")
        print(f"Fetching: {FORM_URL}\n")
        fields = fetch_form_fields(FORM_URL)
        if fields:
            print(f"✅ Successfully parsed {len(fields)} fields:\n")
            print(json.dumps(fields, indent=2))
        else:
            print("❌ No fields found. Form may need login or selector needs update.")
    else:
        # ── NORMAL MODE: run + schedule ────────────────────────────
        check_form()
        schedule.every().day.at("08:00").do(check_form)
        schedule.every().day.at("12:00").do(check_form)
        schedule.every().day.at("16:00").do(check_form)
        schedule.every().day.at("20:00").do(check_form)
        print("Scheduler running. Checks at 8am, 12pm, 4pm, 8pm. Press Ctrl+C to stop.")
        while True:
            schedule.run_pending()
            time.sleep(30)