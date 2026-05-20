"""
Groq API client — uses meta-llama/llama-4-scout-17b-16e-instruct
Supports text, vision (base64 image), and Whisper transcription.
"""

import os
import io
import httpx
import logging
from groq import AsyncGroq

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
MODEL        = "meta-llama/llama-4-scout-17b-16e-instruct"  # best free Llama 4 Scout

_client = AsyncGroq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are EduBot, an expert AI tutor for students from school to university level.

STRICT RULES:
1. Always answer in clear, step-by-step format.
2. For ALL mathematical, physics, or chemistry expressions use proper LaTeX formatting:
   - Inline math: \\( ... \\)
   - Display/block math: \\[ ... \\]
   - Never write equations in plain English. 
     BAD:  "x squared plus y squared equals r squared"
     GOOD: \\( x^2 + y^2 = r^2 \\)
3. Structure every solution with numbered steps.
4. After solving, add a brief "Key Concept" note.
5. Use Telegram Markdown where helpful (bold, italic, code).
6. If a diagram would help, say: "📊 [DIAGRAM: <description>]" on its own line.
7. Be encouraging but stay focused on academics.
"""

async def ask_groq(question: str, image_b64: str | None = None) -> str:
    """Send question (+ optional image) to Llama 4 Scout and return answer."""
    try:
        if image_b64:
            # Vision message
            user_content = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}",
                    },
                },
                {"type": "text", "text": question},
            ]
        else:
            user_content = question

        response = await _client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_content},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
        return response.choices[0].message.content

    except Exception as e:
        logger.error("Groq API error: %s", e)
        raise


async def transcribe_audio(audio_buf: io.BytesIO) -> str:
    """Transcribe audio using Groq Whisper."""
    try:
        audio_buf.seek(0)
        transcription = await _client.audio.transcriptions.create(
            file=("audio.ogg", audio_buf, "audio/ogg"),
            model="whisper-large-v3-turbo",
            response_format="text",
        )
        return transcription.strip()
    except Exception as e:
        logger.error("Whisper transcription error: %s", e)
        raise
