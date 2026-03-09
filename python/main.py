import re
import json
import time
import urllib.request
import threading
from arduino.app_utils import App, Bridge
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.dbstorage_sqlstore import SQLStore 

# Webhook config — set WEBHOOK_TYPE to "discord" or "teams"
WEBHOOK_TYPE = "discord"
WEBHOOK_URL = ""
ui = WebUI() #To secure the panel during implementation, add addr="127.0.0.1" to the webui function.
db = SQLStore("gsm_data.db")

if hasattr(db, 'start'):
    db.start()

def init_db():
    db.execute_sql('''CREATE TABLE IF NOT EXISTS sms_logs
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   data TEXT,
                   timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    db.execute_sql('''CREATE TABLE IF NOT EXISTS sms_messages
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   sender TEXT,
                   content TEXT,
                   timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

init_db()

def _build_payload(sender, content):
    if WEBHOOK_TYPE == "teams":
        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions", #boilerplate
            "summary": "New SMS",
            "themeColor": "0076D7",
            "sections": [{
                "activityTitle": "📨 New SMS received",
                "facts": [
                    {"name": "From", "value": sender},
                    {"name": "Content", "value": content}
                ]
            }]
        }
    # discord (default)
    return {
        "content": f"📨 **NEW SMS!**\n**From:** `{sender}`\n**Content:** {content}"
    }

def send_webhook(sender, content):
    if not WEBHOOK_URL:
        return

    try:
        payload = _build_payload(sender, content)
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (Powiadomski)'}
        )
        urllib.request.urlopen(req, timeout=5)
        print(f"[WEBHOOK] Notification sent via {WEBHOOK_TYPE}!")
    except Exception as e:
        print(f"[WEBHOOK ERROR] Failed to send ({WEBHOOK_TYPE}): {e}")

def on_gsm_rx(data):
    data_str = data.strip()
    if not data_str:
        return
        
    print(f"[MCU RAW] {data_str}")
    db.execute_sql("INSERT INTO sms_logs (data) VALUES (?)", (data_str,))
    
    if "+CMTI:" in data_str:
        match = re.search(r'\+CMTI:\s*"[^"]+",\s*(\d+)', data_str)
        if match:
            index = match.group(1)
            print(f"[AUTO] NEW MESSAGE {index}. Download...")
            Bridge.notify("send_at", f"AT+CMGR={index}\r\n")
            
    elif "+CMGR:" in data_str:
        match = re.search(r'\+CMGR:\s*"[^"]*"\s*,\s*"([^"]+)"[^\n]*\n(.*?)(?:\r\n\r\nOK|\r\nOK|$)', data_str, re.DOTALL)
        if match:
            sender = match.group(1)
            content = match.group(2).strip()
            print(f"[SMS] From: {sender} | Content: {content}")
            
            db.execute_sql("INSERT INTO sms_messages (sender, content) VALUES (?, ?)", (sender, content))
            
            threading.Thread(target=send_webhook, args=(sender, content), daemon=True).start()

Bridge.provide("gsm_rx", on_gsm_rx)

CLEANUP_INTERVAL_HOURS = 6

def gsm_cleanup_loop():
    while True:
        time.sleep(CLEANUP_INTERVAL_HOURS * 3600)
        print(f"[CLEANUP] Deleting all SMS from GSM module (AT+CMGD=1,4)...")
        Bridge.notify("send_at", "AT+CMGD=1,4\r\n")

threading.Thread(target=gsm_cleanup_loop, daemon=True).start()

def get_logs_api():
    rows = db.execute_sql("SELECT timestamp, data FROM sms_logs ORDER BY id DESC")
    if not rows: rows = []
    return {"logs": [{"time": r["timestamp"], "data": r["data"]} for r in rows]}

def get_sms_api():
    rows = db.execute_sql("SELECT timestamp, sender, content FROM sms_messages ORDER BY id DESC")
    if not rows: rows = []
    return {"sms": [{"time": r["timestamp"], "sender": r["sender"], "content": r["content"]} for r in rows]}

def send_command_api(cmd: str):
    print(f"[WWW -> MCU] SEND AT COMMAND: {cmd}")
    Bridge.notify("send_at", cmd + "\r\n")
    return {"status": "success"}

def clear_db_api():
    """Clean DB"""
    print("[WWW] CLEAN DB...")
    db.execute_sql("DELETE FROM sms_logs")
    db.execute_sql("DELETE FROM sms_messages")
    return {"status": "success", "message": "DONE"}

def export_db_api():
    """Export content from DB."""
    logs = db.execute_sql("SELECT timestamp, data FROM sms_logs ORDER BY id ASC")
    sms = db.execute_sql("SELECT timestamp, sender, content FROM sms_messages ORDER BY id ASC")
    
    if not logs: logs = []
    if not sms: sms = []
    
    return {
        "logs": [{"time": r["timestamp"], "data": r["data"]} for r in logs],
        "sms": [{"time": r["timestamp"], "sender": r["sender"], "content": r["content"]} for r in sms]
    }


ui.expose_api("GET", "/api/logs", get_logs_api)
ui.expose_api("GET", "/api/sms", get_sms_api)
ui.expose_api("POST", "/api/send", send_command_api)
ui.expose_api("POST", "/api/clear", clear_db_api)
ui.expose_api("GET", "/api/export", export_db_api)

print("Aplication RUN!")
App.run(user_loop=lambda: None)