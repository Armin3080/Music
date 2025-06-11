from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes,
    CallbackQueryHandler, filters
)
import os
import json
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TOKEN = "6654800068:AAGNhkRs39HWR6D3B3Iu8yOzJCgbuH7S7sk"

# ───── دستور start با دکمه‌های شیشه‌ای ─────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("🎬 لینک نمونه ویدیو", url="https://www.xnxx.com/video-example")],
        [InlineKeyboardButton("📘 راهنما", callback_data="help")],
        [InlineKeyboardButton("📩 ارتباط با ما", url="https://t.me/YourUsername")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "سلام! به ربات دانلود خوش اومدی 🤖\n\nلطفاً لینک ویدیو رو بفرست یا یکی از گزینه‌های زیر رو انتخاب کن:",
        reply_markup=reply_markup
    )

# ───── هندل کلیک روی دکمه‌های شیشه‌ای ─────
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "help":
        await query.edit_message_text(
            text="📘 راهنما:\n\nلینک یک ویدیوی معتبر از سایت رو برای ربات بفرست، ربات خودش ویدیو رو استخراج و برات می‌فرسته."
        )

# ───── دانلود و ارسال ویدیو از لینک ─────
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    chat_id = update.message.chat_id

    if not text.startswith("http"):
        await update.message.reply_text("⚠️ لطفاً فقط لینک معتبر ویدیو رو بفرست.")
        return

    response = get_request_with_retry(text)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        video_url = extract_video_url(soup)
        if video_url:
            await send_video_from_url(chat_id, video_url, context)
        else:
            await context.bot.send_message(chat_id=chat_id, text='❌ ویدیویی یافت نشد.')
    else:
        await context.bot.send_message(chat_id=chat_id, text='⚠️ لینک قابل دسترسی نیست.')

# ───── استخراج لینک ویدیو ─────
def extract_video_url(soup):
    script_tags = soup.find_all('script', type='application/ld+json')
    for script in script_tags:
        try:
            data = json.loads(script.string)
            if '@type' in data and data['@type'] == 'VideoObject' and 'contentUrl' in data:
                if data['contentUrl'].startswith("https://cdn77-vid-mp4.xnxx-cdn.com"):
                    return data['contentUrl']
        except Exception as e:
            print(f"خطا در استخراج لینک ویدیو: {e}")
    return None

# ───── ارسال ویدیو ─────
async def send_video_from_url(chat_id, video_url, context):
    file_name = "video.mp4"
    try:
        video_response = get_request_with_retry(video_url, stream=True)
        if video_response.status_code == 200:
            with open(file_name, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=1024):
                    f.write(chunk)

            with open(file_name, 'rb') as video_file:
                await context.bot.send_video(chat_id=chat_id, video=video_file, timeout=180)

            await context.bot.send_message(chat_id=chat_id, text='✅ ویدیو با موفقیت ارسال شد.')
        else:
            await context.bot.send_message(chat_id=chat_id, text='❌ خطا در دانلود ویدیو.')
    except Exception as e:
        print(f"Error sending video: {e}")
        await context.bot.send_message(chat_id=chat_id, text='❌ خطا در ارسال ویدیو.')
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)

# ───── ریکوئست با Retry ─────
def get_request_with_retry(url, stream=False):
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session.get(url, timeout=30, stream=stream)

# ───── اجرای ربات ─────
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    print("✅ ربات فعال شد. منتظر دریافت لینک هستم...")
    app.run_polling()

if __name__ == '__main__':
    main()

