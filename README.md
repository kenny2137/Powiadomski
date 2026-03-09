# 📳 Powiadomski

Powiadomski is an SMS notification gateway built on Arduino UNO Q. It captures incoming text messages via a GSM module, stores them in a local database, displays them in a web panel, and optionally forwards them to Discord or Microsoft Teams.

---

## Hardware Required

- Arduino UNO Q
- SIMCOM SIM7670E (or compatible A7670E) GSM module with an active SIM card
- Jumper wires

---

## Wiring

Connect the GSM module to Arduino UNO Q using the hardware Serial pins:

| Arduino UNO Q | GSM Module |
|---------------|------------|
| Pin 0 (RX)    | TX         |
| Pin 1 (TX)    | RX         |
| GND           | GND        |
| 5V            | 5V         |

> **Note:** Disconnect the GSM module from pins 0/1 before uploading the sketch, then reconnect after uploading is complete.

---

## Prerequisites

- [Arduino App Lab](https://lab.arduino.cc/) installed and running

---

## Setup

### 1. Import the project into Arduino App Lab

1. Download this repository as a `.zip` file
2. Open **Arduino App Lab**
3. On the home screen, click **Import Project**
4. Select the downloaded `.zip` file
5. The project will open and be ready to run

### 2. (Optional) Configure webhook notifications

Open `python/main.py` and edit the two lines at the top:

```python
WEBHOOK_TYPE = "discord"   # or "teams"
WEBHOOK_URL  = ""          # paste your webhook URL here
```

**Getting a Discord webhook URL:**
1. Open your Discord server → channel settings → Integrations → Webhooks
2. Click *New Webhook*, copy the URL and paste it into `WEBHOOK_URL`

**Getting a Teams webhook URL:**
1. In Teams, go to the channel → Manage channel → Connectors
2. Add *Incoming Webhook*, copy the URL and paste it into `WEBHOOK_URL`
3. Set `WEBHOOK_TYPE = "teams"`

Leave `WEBHOOK_URL` empty to disable notifications.

### 3. (Optional) Restrict panel access to localhost only

In `python/main.py`, change:

```python
ui = WebUI()
```

to:

```python
ui = WebUI(addr="127.0.0.1")
```

This makes the web panel accessible only from the computer the Arduino is plugged into.

### 4. Run the app

Click **Run** in Arduino App Lab. The app will:
- Flash the sketch to the Arduino
- Start the Python backend
- Open the web panel automatically

---

## Web Panel

The panel is available at `http://localhost:7000` and provides:

| Feature | Description |
|---|---|
| **INBOX** | All received SMS messages with sender and timestamp |
| **RAW DATA** | Raw AT command responses from the GSM module |
| **Send AT command** | Manually send any AT command to the module |
| **Export** | Download all data as a JSON file |
| **Clean DB** | Delete all stored messages and logs |

---

## Configuration Reference

All configurable options are at the top of `python/main.py`:

| Variable | Default | Description |
|---|---|---|
| `WEBHOOK_TYPE` | `"discord"` | Platform to send notifications to (`"discord"` or `"teams"`) |
| `WEBHOOK_URL` | `""` | Webhook URL — leave empty to disable |
| `CLEANUP_INTERVAL_HOURS` | `6` | How often to delete SMS messages from the GSM module memory |

---

## How It Works

```
SIM card receives SMS
       ↓
GSM module sends +CMTI notification via UART
       ↓
Arduino forwards it to Python via USB bridge
       ↓
Python fetches the full message (AT+CMGR)
       ↓
SMS is stored in SQLite and shown in the web panel
       ↓
(Optional) Notification sent to Discord / Teams
```
