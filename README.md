# ⚡ Electricity Price Notifier (Denmark - DK2)

An automated, serverless electricity price alert service designed to run for free on **GitHub Actions**. It queries official Danish spot prices from **Energi Data Service (Energinet)** every afternoon at 13:30 CET, analyzes the upcoming 24 hours, and sends a formatted notification directly to your **WhatsApp** via CallMeBot.

---

## 🌟 Features

- **All-Inclusive Consumer Pricing**: Calculates the exact price you pay on your bill (Spot Price + Radius Tarifmodel 3.0 + Energinet Transmission + Elafgift + 25% Moms).
- **Top 3 Cheapest Hours**: Instantly see tomorrow's cheapest hours to schedule heavy appliances (laundry, dishwasher, EV charging).
- **Hours Below 1.00 kr/kWh**: Automatically groups consecutive cheap hours into clear time ranges (e.g. `08:00 - 18:00`).
- **Negative Price Alert**: Flags any hours where spot prices drop below 0.00 kr.
- **Zero Cost (GitHub Free Plan)**: Runs in ~20 seconds per day, consuming less than 15 minutes per month.
- **Zero New Phone Apps**: Delivered directly to your normal WhatsApp app.

---

## 📱 Sample WhatsApp Alert

```text
⚡ Electricity Forecast (DK2) ⚡
📅 Sunday, 27. Sep 2026

📉 Top Cheapest Hours:
1. 14:00 - 15:00 → 0.01 kr (Total: 0.36 kr)
2. 15:00 - 16:00 → 0.01 kr (Total: 0.36 kr)
3. 13:00 - 14:00 → 0.01 kr (Total: 0.37 kr)

🟢 Hours Below 1 kr/kWh (Spot):
• 08:00 - 18:00 (Avg spot: 0.25 kr → Total: 0.70 kr)
• 23:00 - 00:00 (Avg spot: 1.00 kr → Total: 1.60 kr)

📊 Daily Overview:
• Spot Avg: 0.81 kr (Total: 1.40 kr)
• Spot Range: 0.01 – 1.37 kr (Total: 0.36 – 2.31 kr)

💡 Spot: Energi Data Service | Total: Radius + Tax + 25% Moms
```

---

## 🚀 Setup Guide

### Step 1: Get Your Free CallMeBot WhatsApp API Key (takes 1 minute)

1. Add the CallMeBot bot number to your phone contacts:
   - **Phone**: `+34 694 26 48 06` (or check [CallMeBot](https://www.callmebot.com/blog/free-api-whatsapp-messages/) if updated)
   - Name it **CallMeBot**.
2. Open WhatsApp and send this exact text message to that contact:
   ```text
   I allow callmebot to send me messages
   ```
3. Within 1–2 minutes, the bot will reply with your personal **API Key**:
   > *"API Activated for your phone number. Your APIKEY is XXXXXX"*

---

### Step 2: Push to GitHub & Add Secrets

1. Initialize git and push this folder to your GitHub repository (either public or private):
   ```bash
   git init
   git add .
   git commit -m "feat: electricity price notification workflow"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/electricity-price-notification.git
   git push -u origin main
   ```

2. Go to your GitHub repository in your browser:
   - Navigate to **Settings** → **Secrets and variables** → **Actions**.
   - Click **New repository secret** and add:
     - `CALLMEBOT_PHONE`: Your phone number in international format **without** `+` or spaces (e.g. `4512345678` for a Danish mobile).
     - `CALLMEBOT_API_KEY`: The API key you received from the bot.

---

### Step 3: Test It Manually

1. In your GitHub repository, click the **Actions** tab.
2. Under **Workflows** on the left, select **Daily Electricity Price Alert**.
3. Click the **Run workflow** button on the right and confirm.
4. Within 30 seconds, you will receive a WhatsApp message on your phone!

---

## ⚙️ Configuration & Customization

All defaults can be adjusted either via `.github/workflows/daily-price-alert.yml` or through a local `.env` file:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `PRICE_AREA` | `DK2` | `DK2` (Zealand / Greater Copenhagen) or `DK1` (Jutland / Funen) |
| `CHEAP_THRESHOLD_DKK` | `1.0` | Threshold in DKK/kWh below which hours are grouped and reported |
| `TOP_CHEAPEST_COUNT` | `3` | How many cheapest hours to list in the top ranking |
| `INCLUDE_TARIFFS` | `true` | When true, calculates and displays all-inclusive price alongside spot price |
| `GRID_OPERATOR` | `Radius` | Local grid company for Tarifmodel 3.0 (e.g. `Radius` for Greater Copenhagen) |
| `NOTIFIERS_ENABLED` | `whatsapp` | Channels to send to (`whatsapp`, or `whatsapp,email`) |

### Customizing the Message Template
The message layout and wording are defined in [src/formatter.py](file:///c:/Users/jonsa/LLM/electricity-price-notification/src/formatter.py). You can easily modify icons, add custom tips, or change wording to Danish if desired.

---

## 💻 Local Development & Testing

You can test the analyzer and message generation locally without dispatching any messages using `--dry-run`:

```bash
# 1. Run unit tests
python -m unittest tests/test_components.py

# 2. Run dry run (prints formatted message to terminal)
python -m src.main --dry-run

# 3. Test a specific date or zone
python -m src.main --date 2026-09-27 --zone DK2 --dry-run
```

---

## 📧 Future Extension: Adding Email Notifications

When you want to add Email notifications:
1. Set `NOTIFIERS_ENABLED: "whatsapp,email"` in your workflow environment.
2. Add your SMTP secrets (`EMAIL_SMTP_HOST`, `EMAIL_SMTP_USER`, `EMAIL_SMTP_PASSWORD`, `EMAIL_TO`) to GitHub Repository Secrets.
3. The built-in [src/notifiers/email.py](file:///c:/Users/jonsa/LLM/electricity-price-notification/src/notifiers/email.py) will automatically dispatch the email alongside WhatsApp.
