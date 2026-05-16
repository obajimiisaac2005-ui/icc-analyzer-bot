import os
import logging
import requests
import base64
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ── LOGGING ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── CONFIG ───────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY  = os.environ.get("GEMINI_API_KEY")
GEMINI_URL      = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# ── ICC SYSTEM PROMPT ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a master ICC (Indication, Correction, Continuation) trading analyst with deep expertise in institutional price action and the complete ICC methodology by Trades by Sci.

CORE PHILOSOPHY
Markets move in 3-phase cycles driven by institutional order flow. ICC traders REACT to what institutions have already done. The only rule: DO NOT BECOME LIQUIDITY.

PHASE 1 INDICATION
Price aggressively breaks a MAJOR swing high (bullish) or swing low (bearish) on H1/H4. Only SWING breaks count. MSS is the strongest form. Fakeouts occur when price breaks then immediately reverses — LIQUIDITY GRAB, flip the bias. DO NOT ENTER during indication.

PHASE 2 CORRECTION
Price retraces into the AOI / Cushion Zone to trap FOMO traders. Watch 15M for CHoCH. CHoCH for buys: HIGHER HIGH on 15M after lower highs during correction. CHoCH for sells: LOWER LOW on 15M after higher lows. DO NOT ENTER during correction.

PHASE 3 CONTINUATION — THE ONLY ENTRY ZONE
ALL entries taken here only. Entry types: AGGRESSIVE (CHoCH candle close), CONSERVATIVE (confirming candle), BREAK AND RETEST (full retest of correction level).

AOI AREA OF INTEREST
Zone where correction ends. Watch for INDUCEMENTS (fake equal highs/lows to trap retail).

SETUP GRADING
A+: H4/H1 indication + clean AOI tap + 15M CHoCH + liquidity sweep + London/NY session.
B: H1 indication + AOI tap + CHoCH but missing one confluence.
NO TRADE: Ranging, unclear structure, RRR below 1:3.

TIMEFRAME TOP-DOWN
H4/H1: Indication only, sets bias, never enter.
H1/15M: Watch Correction, mark AOI.
15M/5M: Execute entry, CHoCH confirmation.

RISK MANAGEMENT NON-NEGOTIABLE
MINIMUM RRR 1:3. Max 2 trades/session. Stop after 2 losses. Move SL to breakeven after 1R. NEVER widen SL.

STOP LOSS
Aggressive: just beyond 15M CHoCH swing.
Conservative: beyond entire HTF AOI.

TAKE PROFIT
TP1: 1:3 RRR minimum (3x SL distance).
TP2: 1:5 RRR, next structure level.
TP3: Runner, previous major high/low.

OUTPUT FORMAT — FOLLOW EXACTLY. ALWAYS give SPECIFIC PRICE NUMBERS. Never write N/A.

📊 MARKET OVERVIEW
• Pair/Asset: [identify or Unknown]
• Timeframe: [identify]
• Session: [London / New York / Asian / Unknown]

📈 TREND ANALYSIS
• Structure: UPTREND / DOWNTREND / RANGING
• HTF Bias: Bullish / Bearish / Neutral
• Character: Trending / Choppy / Transitioning

⚡ ICC PHASE
• Current Phase: INDICATION / CORRECTION / CONTINUATION / RANGING
• Phase Quality: Clean / Choppy / Unclear
• Fakeout Risk: Low / Medium / High — [reason]

🎯 INDICATION
• Level: [specific price]
• Type: Break of Structure / MSS / Continuation
• Strength: Strong / Moderate / Weak — [reason]

🔄 CORRECTION
• Correction Zone AOI: [price range]
• Quality: Clean / Choppy / Deep
• CHoCH Level: [specific price]
• Liquidity Grab: Yes/No — [explain]
• Inducements: Yes/No — [explain]

✅ SETUP GRADE
• Grade: A+ / B / C / NO TRADE
• Reason: [confluences present or missing]

💹 TRADE EXECUTION
• Bias: BUY / SELL / NO TRADE
• Entry Type: Aggressive / Conservative / Break and Retest
• ENTRY: [specific price]
• STOP LOSS: [specific price] | Risk: [X pips]
• TP1 (1:3): [specific price] | +[X pips]
• TP2 (1:5): [specific price] | +[X pips]
• TP3 RUNNER: [specific price] | +[X pips]
• Breakeven: Move SL to entry after [price]

⚠️ INVALIDATION
• Invalid if price closes: [specific level]

🧠 ANALYST NOTES
[3-4 sentences on ICC reasoning, liquidity, what confirms or weakens the setup, key cautions]

If market is ranging or RRR below 1:3, clearly state NO TRADE and explain why."""


# ── GEMINI API CALL ───────────────────────────────────────────────────────────

def analyze_with_gemini(image_bytes: bytes, mime_type: str) -> str:
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "contents": [{
            "parts": [
                {
                    "text": SYSTEM_PROMPT + "\n\nAnalyze this chart using the complete ICC protocol. Follow the output format exactly. Give specific price levels for every field."
                },
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": b64_image
                    }
                }
            ]
        }],
        "generationConfig": {
            "maxOutputTokens": 1500,
            "temperature": 0.2
        }
    }

    response = requests.post(GEMINI_URL, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


# ── COMMAND HANDLERS ──────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Welcome to ICC Analyzer Pro!*\n\n"
        "I analyze forex and crypto charts using the *ICC strategy*\n"
        "Indication → Correction → Continuation\n\n"
        "📊 *Just send me a chart screenshot and I'll give you:*\n"
        "• Current ICC phase\n"
        "• Trade bias — BUY / SELL / NO TRADE\n"
        "• Specific Entry, Stop Loss and 3 TP levels\n"
        "• Minimum 1:3 RRR enforced\n"
        "• Setup grade — A+ / B / C\n"
        "• Invalidation level\n\n"
        "⚡ *Best pairs:* XAUUSD · NAS100 · EURUSD · GBPUSD\n"
        "⚡ *Best sessions:* London · New York\n\n"
        "Send your chart now to get started!",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *ICC Quick Guide*\n\n"
        "🔵 *INDICATION* — Break of major swing H/L on H1-H4. Mark it. Do NOT enter.\n\n"
        "🟡 *CORRECTION* — Pullback into AOI trapping FOMO traders. Watch 15M for CHoCH. Do NOT enter.\n\n"
        "🟢 *CONTINUATION* — CHoCH confirmed. Trend resumes. Your ONLY entry zone.\n\n"
        "🔴 *RANGING* — Equal highs and lows. No clear structure. Stay out completely.\n\n"
        "📏 *Non-negotiable rules:*\n"
        "• Minimum 1:3 RRR always\n"
        "• Max 2 trades per session\n"
        "• Stop after 2 consecutive losses\n"
        "• Move SL to breakeven after 1R\n"
        "• NEVER widen your stop loss\n\n"
        "Send a chart screenshot to get your analysis!",
        parse_mode="Markdown"
    )

async def analyze_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Running ICC analysis on your chart...")

    try:
        # Get highest resolution photo
        photo    = update.message.photo[-1]
        file     = await context.bot.get_file(photo.file_id)
        img_bytes = await file.download_as_bytearray()

        # Call Gemini
        analysis = analyze_with_gemini(bytes(img_bytes), "image/jpeg")

        await msg.delete()

        # Send in chunks if needed (Telegram 4096 char limit)
        if len(analysis) > 4000:
            for i in range(0, len(analysis), 4000):
                await update.message.reply_text(analysis[i:i+4000])
        else:
            await update.message.reply_text(analysis)

    except requests.exceptions.HTTPError as e:
        await msg.delete()
        logger.error(f"Gemini API error: {e}")
        await update.message.reply_text(
            "❌ Analysis failed — Gemini API error.\n"
            "Please check your GEMINI_API_KEY in Railway variables."
        )
    except Exception as e:
        await msg.delete()
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "❌ Something went wrong. Please send a clear chart screenshot and try again."
        )

async def handle_non_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 Send me a *chart screenshot* to get your ICC analysis.\n"
        "Type /help to learn how the strategy works.",
        parse_mode="Markdown"
    )


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN environment variable is not set")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is not set")

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help",  help_command))
    app.add_handler(MessageHandler(filters.PHOTO, analyze_chart))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_non_image))

    logger.info("ICC Analyzer Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
