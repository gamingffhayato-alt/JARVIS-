# 📚 EduBot AI — Telegram Education Bot

> Powered by **Llama 4 Scout** via Groq API | Deployed on Railway

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔢 Math & Science | Proper LaTeX/mathematical formatting — never plain English |
| 🖼️ Image Reading | Send a photo of a question — bot solves it |
| 🎤 Voice Support | Send voice notes — auto-transcribed via Whisper |
| 📄 PDF Solutions | Step-by-step solutions exported as formatted PDF |
| 📊 Scientific Diagrams | Cell, DNA, circuits, waves, free-body, photosynthesis, etc. |
| 🚫 Anti-Masti Filter | Off-topic questions get: "PTA HAI BC PADAI KRNI HAI PR MASTI DEKHO BCC" |
| 🚨 Error Reporting | All errors sent to your monitoring bot with full traceback |

---

## 🚀 Deploy on Railway

### Step 1 — Fork / Upload this repo
Push this folder to a GitHub repository.

### Step 2 — Create Railway project
1. Go to [railway.app](https://railway.app)
2. New Project → Deploy from GitHub repo
3. Select your repo

### Step 3 — Set Environment Variables
In Railway dashboard → your service → **Variables**, add:

```
BOT_TOKEN          = <your EduBot telegram bot token>
GROQ_API_KEY       = <your Groq API key from console.groq.com>
ERROR_BOT_TOKEN    = <token of your error-monitoring bot>
ERROR_CHAT_ID      = <chat_id that should receive errors>
WEBHOOK_URL        = https://your-app.up.railway.app  (optional, for webhook mode)
```

### Step 4 — Deploy
Railway will auto-detect `Procfile` and run `python bot.py`.

---

## 🤖 Bot Commands

| Command | What it does |
|---|---|
| `/start` | Welcome message |
| `/help` | Show help |
| `/pdf` | Get last answer as a PDF |
| `/diagram <topic>` | Generate a scientific diagram |

---

## 📐 Supported Diagrams

- Plant / Animal Cell
- DNA Double Helix
- Photosynthesis
- Electric Circuit (with Ohm's Law)
- Wave Properties
- Free Body Diagram
- Atom / Bohr Model
- Mitosis stages
- Math function graphs (parabola, sine, cosine, exponential…)
- Water Cycle
- Heart & Blood Flow
- Generic Concept Map (fallback for any topic)

---

## 🔑 Getting API Keys

### Groq API (Free)
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up → API Keys → Create key
3. The bot uses **`meta-llama/llama-4-scout-17b-16e-instruct`** (best free model)

### Telegram Bot Tokens
1. Open Telegram → search `@BotFather`
2. `/newbot` → follow prompts → copy the token
3. Repeat for the error-monitoring bot

### Get Your Chat ID
1. Start a chat with `@userinfobot` on Telegram
2. It will reply with your numeric chat ID

---

## 📁 Project Structure

```
edubot/
├── bot.py              # Main bot logic & handlers
├── groq_client.py      # Groq API (Llama 4 Scout + Whisper)
├── pdf_generator.py    # ReportLab PDF with LaTeX math rendering
├── diagram_generator.py # matplotlib scientific diagrams
├── requirements.txt
├── Procfile            # Railway start command
├── railway.toml        # Railway config
└── .env.example        # Environment variable template
```

---

## 🛠️ Local Development

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in .env values
python bot.py
```

---

## 📊 Math Formatting

The bot uses proper mathematical notation:
- Inline: `\( x^2 + y^2 = r^2 \)`
- Display blocks: `\[ \int_0^\infty e^{-x} dx = 1 \]`
- PDF renders these via matplotlib mathtext (no LaTeX installation needed)

---

*Bas padhai karo! 📚*
