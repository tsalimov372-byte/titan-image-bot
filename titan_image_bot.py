"""
Titan AI - Telegram rasm generatsiya boti
Pollinations.ai API orqali matndan rasm yaratadi (kalitsiz, bepul)

O'rnatish:
    pip install python-telegram-bot httpx

Ishga tushirish:
    1. @BotFather orqali bot yarating va tokenni oling
    2. Pastda BOT_TOKEN o'rniga o'z tokeningizni qo'ying
    3. python titan_image_bot.py
"""

import urllib.parse
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ==== SOZLAMALAR ====
BOT_TOKEN = "672559993:AAFCa3Fej2Aq17_I9pZxJdBIh3l1ah8D5M"  # @BotFather'dan olingan token
POLLINATIONS_URL = "https://image.pollinations.ai/prompt"

# Uslub tanlanganda promptga qo'shiladigan so'zlar
STYLES = {
    "realistic": ("📷 Realistik", "highly detailed, photorealistic, 8k, sharp focus"),
    "anime": ("🎌 Anime", "anime style, studio ghibli, vibrant colors"),
    "disney": ("🏰 Disney-Pixar", "disney pixar 3d animation style, colorful"),
    "oil": ("🖼️ Moyli rasm", "oil painting, canvas texture, fine art"),
}

# Foydalanuvchining oxirgi tanlagan uslubi (xotirada, oddiy versiya)
user_styles: dict[int, str] = {}


def style_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(label, callback_data=f"style:{key}")]
        for key, (label, _) in STYLES.items()
    ]
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ <b>Titan AI Rasm Bot</b>ga xush kelibsiz!\n\n"
        "🎨 Menga xohlagan rasmingiz tavsifini yozing va men uni sun'iy intellekt "
        "yordamida chizib beraman.\n\n"
        "1️⃣ Avval uslubni tanlang\n"
        "2️⃣ Keyin rasm tasvirini yozing\n\n"
        "Masalan: <i>\"qorli tog'lar ustida quyosh botishi\"</i>",
        parse_mode="HTML",
        reply_markup=style_keyboard(),
    )


async def choose_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    style_key = query.data.split(":", 1)[1]
    user_styles[query.from_user.id] = style_key
    label, _ = STYLES[style_key]

    await query.edit_message_text(
        f"✅ Uslub tanlandi: <b>{label}</b>\n\n"
        f"🖌️ Endi menga rasm tavsifini yozing.\n"
        f"Masalan: <i>\"qorli tog'lar ustida quyosh botishi\"</i>",
        parse_mode="HTML",
    )


async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        prompt = " ".join(context.args)
    else:
        prompt = update.message.text

    if not prompt or not prompt.strip():
        await update.message.reply_text("✍️ Iltimos, rasm uchun matn (prompt) yozing.")
        return

    user_id = update.message.from_user.id
    style_key = user_styles.get(user_id, "realistic")
    style_label, style_suffix = STYLES[style_key]

    final_prompt = f"{prompt}, {style_suffix}"

    waiting_msg = await update.message.reply_text(
        f"🖌️ <b>{style_label}</b> uslubida rasm yaratilmoqda...\n"
        f"⏳ Biroz kuting (10-30 soniya)",
        parse_mode="HTML",
    )

    try:
        encoded_prompt = urllib.parse.quote(final_prompt)
        image_url = f"{POLLINATIONS_URL}/{encoded_prompt}?width=1024&height=1024&nologo=true"

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(image_url)

        if response.status_code != 200:
            await waiting_msg.edit_text("❌ Rasm generatsiya qilishda xatolik yuz berdi. Qaytadan urinib ko'ring.")
            return

        await update.message.reply_photo(
            photo=response.content,
            caption=(
                f"✅ <b>Tayyor!</b>\n"
                f"🎨 Uslub: {style_label}\n"
                f"📝 Tavsif: {prompt}"
            ),
            parse_mode="HTML",
            reply_markup=style_keyboard(),
        )
        await waiting_msg.delete()

    except Exception as e:
        await waiting_msg.edit_text(f"❌ Xatolik: {e}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", generate_image))
    app.add_handler(CallbackQueryHandler(choose_style, pattern=r"^style:"))
    # Oddiy matn yuborilsa ham (komandasiz) rasm generatsiya qilsin
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))

    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
