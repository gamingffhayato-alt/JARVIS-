import os
import io
import logging
import asyncio
import traceback
import base64
import httpx
import json
import re
from datetime import datetime
from telegram import Update, InputFile
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from pdf_generator import generate_pdf_solution
from diagram_generator import generate_diagram
from groq_client import ask_groq, transcribe_audio

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────
BOT_TOKEN       = os.environ["BOT_TOKEN"]
ERROR_BOT_TOKEN = os.environ["ERROR_BOT_TOKEN"]
ERROR_CHAT_ID   = os.environ["ERROR_CHAT_ID"]

ANTI_MASTI_MSG = (
    "PTA HAI BC PADAI KRNI HAI PR MASTI DEKHO BCC 📚😤\n\n"
    "Bhai seedha question pooch, main tuhari help karne ke liye hoon — "
    "sirf studies mein! 🎓"
)

STUDY_KEYWORDS = [
    # Sciences
    "math", "physics", "chemistry", "biology", "science", "formula",
    "equation", "theorem", "proof", "derivative", "integral", "matrix",
    "vector", "force", "energy", "velocity", "acceleration", "mass",
    "atom", "molecule", "reaction", "element", "periodic", "cell",
    "dna", "rna", "protein", "evolution", "gravity", "quantum",
    "wave", "frequency", "wavelength", "circuit", "resistance",
    # Engineering
    "engineering", "algorithm", "code", "program", "software",
    "hardware", "network", "data", "structure", "function",
    # Humanities / academics
    "history", "geography", "economics", "literature", "grammar",
    "essay", "analysis", "explain", "define", "what is", "how does",
    "why does", "solve", "calculate", "find", "prove", "derive",
    "question", "problem", "exercise", "homework", "assignment",
    "exam", "test", "study", "learn", "understand", "concept",
    # Hindi/Urdu academic words
    "padhai", "padna", "samjhao", "batao", "kya hai", "kaise",
    "numerics", "numerical", "diagram", "graph", "chart", "plot",
    "pdf", "solution", "answer", "help",
]

def is_study_related(text: str) -> bool:
    """Return True if message looks academic."""
    if not text:
        return True   # media messages are assumed academic
    t = text.lower()
    return any(kw in t for kw in STUDY_KEYWORDS)


# ── Error reporter ───────────────────────────────────────────────────────────
async def report_error(error_text: str, context_info: str = ""):
    """Send error details to the designated error-monitoring bot."""
    try:
        msg = (
            f"🚨 *EduBot Error*\n"
            f"`{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
            f"*Context:* {context_info}\n\n"
            f"```\n{error_text[:3500]}\n```"
        )
        url = f"https://api.telegram.org/bot{ERROR_BOT_TOKEN}/sendMessage"
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(url, json={
                "chat_id": ERROR_CHAT_ID,
                "text": msg,
                "parse_mode": "Markdown",
            })
    except Exception as e:
        logger.error("Could not send error report: %s", e)


# ── /start ───────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *Welcome to EduBot AI* 🤖\n\n"
        "Powered by *Llama 4 Scout* via Groq\n\n"
        "I can help you with:\n"
        "• 🔢 Math problems (with proper LaTeX formatting)\n"
        "• ⚗️ Physics & Chemistry\n"
        "• 🧬 Biology diagrams\n"
        "• 📄 PDF step-by-step solutions\n"
        "• 🎤 Voice question support\n"
        "• 🖼️ Image-based question solving\n\n"
        "Commands:\n"
        "/pdf — Get last answer as a formatted PDF\n"
        "/diagram `<topic>` — Generate a scientific diagram\n"
        "/help — Show this message\n\n"
        "Bas pooch, main hoon na! 💪",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, ctx)


# ── /pdf  ────────────────────────────────────────────────────────────────────
async def cmd_pdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    last = ctx.user_data.get("last_answer")
    last_q = ctx.user_data.get("last_question", "Solution")
    if not last:
        await update.message.reply_text("No recent answer found. Ask a question first!")
        return
    await update.message.reply_text("📄 Generating PDF solution…")
    try:
        pdf_bytes = await asyncio.to_thread(generate_pdf_solution, last_q, last)
        await update.message.reply_document(
            document=InputFile(io.BytesIO(pdf_bytes), filename="solution.pdf"),
            caption="📄 Here's your step-by-step PDF solution!",
        )
    except Exception as e:
        tb = traceback.format_exc()
        await report_error(tb, f"cmd_pdf | user={update.effective_user.id}")
        await update.message.reply_text("❌ Error generating PDF. Reported to admin.")


# ── /diagram ─────────────────────────────────────────────────────────────────
async def cmd_diagram(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(ctx.args) if ctx.args else ctx.user_data.get("last_question", "")
    if not topic:
        await update.message.reply_text("Usage: /diagram <topic>  e.g. `/diagram cell membrane`")
        return
    await update.message.reply_text(f"🎨 Generating diagram for: *{topic}*…", parse_mode="Markdown")
    try:
        img_bytes = await asyncio.to_thread(generate_diagram, topic)
        await update.message.reply_photo(
            photo=InputFile(io.BytesIO(img_bytes), filename="diagram.png"),
            caption=f"📊 Scientific diagram: *{topic}*",
            parse_mode="Markdown",
        )
    except Exception as e:
        tb = traceback.format_exc()
        await report_error(tb, f"cmd_diagram | topic={topic}")
        await update.message.reply_text("❌ Could not generate diagram. Reported.")


# ── Text messages ────────────────────────────────────────────────────────────
async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    if not is_study_related(text):
        await update.message.reply_text(ANTI_MASTI_MSG)
        return

    await update.message.reply_chat_action("typing")
    try:
        answer = await ask_groq(text)
        ctx.user_data["last_question"] = text
        ctx.user_data["last_answer"]   = answer

        # Check if diagram is needed
        diagram_triggers = [
            "diagram", "draw", "sketch", "illustrate", "show",
            "circuit", "cell", "dna", "structure", "graph", "plot"
        ]
        if any(t in text.lower() for t in diagram_triggers):
            try:
                img_bytes = await asyncio.to_thread(generate_diagram, text)
                await update.message.reply_photo(
                    photo=InputFile(io.BytesIO(img_bytes), filename="diagram.png"),
                    caption="📊 Scientific diagram",
                )
            except Exception:
                pass  # diagram failure is non-critical

        await update.message.reply_text(answer, parse_mode="Markdown")
        await update.message.reply_text(
            "💡 Want a detailed PDF solution? Use /pdf",
        )
    except Exception as e:
        tb = traceback.format_exc()
        await report_error(tb, f"handle_text | user={update.effective_user.id} | q={text[:100]}")
        await update.message.reply_text("❌ Something went wrong. Admin notified.")


# ── Photo messages ───────────────────────────────────────────────────────────
async def handle_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_chat_action("typing")
    caption = update.message.caption or "Solve this problem"
    try:
        photo = update.message.photo[-1]
        file  = await ctx.bot.get_file(photo.file_id)
        buf   = io.BytesIO()
        await file.download_to_memory(buf)
        buf.seek(0)

        img_b64 = base64.b64encode(buf.read()).decode()
        answer  = await ask_groq(caption, image_b64=img_b64)

        ctx.user_data["last_question"] = caption
        ctx.user_data["last_answer"]   = answer

        await update.message.reply_text(answer, parse_mode="Markdown")
        await update.message.reply_text("💡 Want a PDF? Use /pdf")
    except Exception as e:
        tb = traceback.format_exc()
        await report_error(tb, f"handle_photo | user={update.effective_user.id}")
        await update.message.reply_text("❌ Could not process image. Admin notified.")


# ── Voice / Audio messages ───────────────────────────────────────────────────
async def handle_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎤 Transcribing your question…")
    try:
        voice = update.message.voice or update.message.audio
        file  = await ctx.bot.get_file(voice.file_id)
        buf   = io.BytesIO()
        await file.download_to_memory(buf)
        buf.seek(0)

        transcript = await transcribe_audio(buf)
        if not transcript:
            await update.message.reply_text("❌ Could not transcribe. Please try again.")
            return

        await update.message.reply_text(f"📝 Heard: *{transcript}*", parse_mode="Markdown")

        if not is_study_related(transcript):
            await update.message.reply_text(ANTI_MASTI_MSG)
            return

        answer = await ask_groq(transcript)
        ctx.user_data["last_question"] = transcript
        ctx.user_data["last_answer"]   = answer

        await update.message.reply_text(answer, parse_mode="Markdown")
        await update.message.reply_text("💡 Want a PDF? Use /pdf")
    except Exception as e:
        tb = traceback.format_exc()
        await report_error(tb, f"handle_voice | user={update.effective_user.id}")
        await update.message.reply_text("❌ Audio processing failed. Admin notified.")


# ── Document (PDF/image file) ────────────────────────────────────────────────
async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    mime = doc.mime_type or ""
    caption = update.message.caption or "Solve / explain this document"

    if mime.startswith("image/"):
        await update.message.reply_chat_action("typing")
        try:
            file  = await ctx.bot.get_file(doc.file_id)
            buf   = io.BytesIO()
            await file.download_to_memory(buf)
            buf.seek(0)
            img_b64 = base64.b64encode(buf.read()).decode()
            answer  = await ask_groq(caption, image_b64=img_b64)
            ctx.user_data["last_question"] = caption
            ctx.user_data["last_answer"]   = answer
            await update.message.reply_text(answer, parse_mode="Markdown")
        except Exception as e:
            tb = traceback.format_exc()
            await report_error(tb, "handle_document/image")
            await update.message.reply_text("❌ Error. Admin notified.")
    else:
        await update.message.reply_text(
            "📎 I can process image files and voice. "
            "For text questions just type them!"
        )


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("pdf",     cmd_pdf))
    app.add_handler(CommandHandler("diagram", cmd_diagram))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO,                   handle_photo))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO,   handle_voice))
    app.add_handler(MessageHandler(filters.Document.ALL,            handle_document))

    port = int(os.environ.get("PORT", 8080))
    webhook_url = os.environ.get("WEBHOOK_URL", "")

    if webhook_url:
        logger.info("Starting webhook on port %s → %s", port, webhook_url)
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url,
            drop_pending_updates=True,
        )
    else:
        logger.info("Starting polling…")
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
