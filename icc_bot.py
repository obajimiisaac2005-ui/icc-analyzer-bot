import os
import logging
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import io

# ── LOGGING ──────────────────────────────────────────────────────────────────
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ── CONFIG ───────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY  = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ── ICC SYSTEM PROMPT ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a master ICC (Indication, Correction, Continuation) trading analyst with deep expertise in institutional price action and the complete ICC methodology by Trades by Sci.

CORE PHILOSOPHY
Markets move in repeatable 3-phase cycles driven by institutional order flow. ICC traders REACT to what institutions have already done. The only rule: DO NOT BECOME LIQUIDITY.

PHASE 1 INDICATION
Price aggressively breaks a MAJOR swing high (bullish) or swing low (bearish) on H1/H4. Only breaks of SWING highs/lows count. A Market Structure Shift (MSS) is the strongest form. Fakeouts occur when price breaks then immediately reverses — this is a LIQUIDITY GRAB, flip the bias. DO NOT ENTER during indication. Just mark it.

PHASE 2 CORRECTION
Price retraces into the Area of Interest (AOI) / Cushion Zone to trap FOMO traders. Watch the 15M chart for CHoCH (Change of Character). CHoCH for buys: price makes a HIGHER HIGH on 15M after making lower highs. CHoCH for sells: price makes a LOWER LOW on 15M after making higher lows. DO NOT ENTER during correction.

PHASE 3 CONTINUATION — THE ONLY ENTRY ZONE
ALL entries taken here only. Three entry types: AGGRESSIVE (enter on CHoCH candle close), CONSERVATIVE (wait for confirming candle), BREAK AND RETEST (wait for full retest).

AREA OF INTEREST AOI
Zone where correction is expected to end. Watch for INDUCEMENTS (fake equal highs/lows to trap retail before continuation).

SETUP GRADING
A+ SETUP: H4/H1 indication + clean AOI tap + 15M CHoCH + liquidity sweep + London/NY session timing.
B SETUP: H1 indication + AOI tap + CHoCH but missing one confluence.
C SETUP / NO TRADE: Ranging market, unclear structure, no HTF confluence.

TIMEFRAME TOP-DOWN
H4/H1: Identify Indication only, sets bias, never enter.
H1/15M: Watch Correction unfold, mark AOI.
15M/5M: Execute entry, look for CHoCH.

DO NOT TRADE WHEN: Market is ranging. RRR below 1:3. Correction is choppy. Asian session for most pairs.

RISK MANAGEMENT NON-NEGOTIABLE
MINIMUM RRR is 1:3. Max 2 trades per session. Stop after 2 consecutive losses. Move SL to breakeven after 1R profit. NEVER widen stop loss.

STOP LOSS PLACEMENT
Aggressive SL: just below/above the 15M CHoCH swing point.
Conservative SL: below/above the entire HTF Area of Interest.
Always place SL beyond nearest swing point including spread.

TAKE PROFIT PLACEMENT
TP1 at 1:3 RRR minimum (3x the SL distance).
TP2 at 1:5 RRR, next major structure level.
TP3 runner at previous major high/low or HTF target.

OUTPUT FORMAT — FOLLOW EXACTLY. ALWAYS give SPECIFIC PRICE NUMBERS. Never write N/A.

📊 MARKET OVERVIEW
• Pair/Asset: [identify or state Unknown]
• Timeframe: [identify from chart]
• Session: [London / New York / Asian / Unknown]

📈 TREND ANALYSIS
• Structure: UPTREND / DOWNTREND / RANGING
• HTF Bias: Bullish / Bearish / Neutral
• Market Character: Trending / Choppy / Transitioning

⚡ ICC PHASE
• Current Phase: INDICATION / CORRECTION / CONTINUATION / RANGING
• Phase Quality: Clean / Choppy / Unclear
• Fakeout Risk: Low / Medium / High — [reason]

🎯 INDICATION
• Indication Level: [specific price]
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
• Reason: [explain confluences]

💹 TRADE EXECUTION
• Bias: BUY / SELL / NO TRADE
• Entry Type: Aggressive / Conservative / Break and Retest
• ENTRY: [specific price]
• STOP LOSS: [specific price] | Risk: [X pips]
• TP1 (1:3): [specific price] | +[X pips]
• TP2 (1:5): [specific price] | +[X pips]
• TP3 RUNNER: [specific price] | +[X pips]
• Breakeven: Move SL to entry after [price] is reached

⚠️ INVALIDATION
• Invalid if price closes: [specific level]

🧠 ANALYST NOTES
[3-4 sentences on ICC reasoning, liquidity grabbed, what confirms/weakens the setup, and key cautions]

If market is ranging or RRR is below 1:3, clearly state NO TRADE and explain exactly why."""


# ── COMMAND HANDLERS ─────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 *Welcome to ICC Analyzer Pro!*\n\n"
        "I analyze forex and crypto charts using the *ICC strategy* "
        "(Indication → Correction → Continuation).\n\n"
        "📊 *How to use:*\n"
        "Simply send me a screenshot of any chart and I'll give you:\n"
        "• Current ICC phase\n"
        "• Trade bias (BUY/SELL/NO TRADE)\n"
        "• Specific Entry, Stop Loss & 3 TP levels\n"
        "• Minimum 1:3 RRR enforced\n"
        "• Setup grade (A+/B/C)\n\n"
        "⚡ *Best pairs:* XAUUSD · NAS100 · EURUSD · GBPUSD\n"
        "⚡ *Best sessions:* London · New York\n\n"
        "Send your chart screenshot now to get started!",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *ICC Strategy Quick Guide*\n\n"
        "🔵 *INDICATION* — Break of major swing H/L on H1-H4. Mark it. Do NOT enter.\n\n"
        "🟡 *CORRECTION* — Pullback into AOI trapping FOMO traders. Watch 15M for CHoCH. Do NOT enter.\n\n"
        "🟢 *CONTINUATION* — CHoCH confirmed. Trend resumes. Your ONLY entry zone.\n\n"
        "🔴 *RANGING* — Equal highs and lows. No clear structure. Stay out completely.\n\n"
        "📏 *Rules:*\n"
        "• Minimum 1:3 RRR always\n"
        "• Max 2 trades per session\n"
        "• Stop after 2 consecutive losses\n"
        "• Move SL to breakeven after 1R hit\n"
        "• NEVER widen your stop loss\n\n"
        "Send a chart screenshot to get your ICC analysis!",
        parse_mode="Markdown"
    )

async def analyze_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming chart screenshots."""
    await update.message.reply_text("⏳ Analyzing your chart with ICC protocol...")

    try:
        # Get the photo (highest resolution)
        photo = update.message.photo[-1]
        file  = await context.bot.get_file(photo.file_id)

        # Download image bytes
        img_bytes = await file.download_as_bytearray()
        image = Image.open(io.BytesIO(img_bytes))

        # Send to Gemini
        response = model.generate_content([
            SYSTEM_PROMPT + "\n\nAnalyze this chart using the complete ICC protocol. Follow the output format exactly. Give specific price levels for every field.",
            image
        ])

        analysis = response.text

        # Split into chunks if too long for Telegram (4096 char limit)
        if len(analysis) > 4000:
            chunks = [analysis[i:i+4000] for i in range(0, len(analysis), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(analysis)

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        await update.message.reply_text(
            "❌ Analysis failed. Please make sure you're sending a clear chart screenshot and try again.\n\n"
            f"Error: {str(e)}"
        )

async def handle_non_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 Please send a *chart screenshot* to get your ICC analysis.\n\n"
        "Type /help to see how the strategy works.",
        parse_mode="Markdown"
    )


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help",  help_command))
    app.add_handler(MessageHandler(filters.PHOTO, analyze_chart))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_non_image))

    logger.info("ICC Analyzer Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
