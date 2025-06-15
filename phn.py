from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, CallbackQueryHandler, filters
)
import yt_dlp
import os
import requests

BOT_TOKEN = '6654800068:AAGNhkRs39HWR6D3B3Iu8yOzJCgbuH7S7sk'

user_video_formats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! لینک ویدیوی Pornhub رو بفرست 🎥")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.message.chat_id

    if "pornhub.com" not in url:
        await update.message.reply_text("فقط لینک‌های pornhub.com پشتیبانی می‌شن ❗")
        return

    await update.message.reply_text("⏳ در حال پردازش ویدیو...")

    try:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = info.get('formats', [])
        video_formats = [f for f in formats if f.get('ext') == 'mp4' and f.get('height')]

        if not video_formats:
            await update.message.reply_text("❌ هیچ کیفیتی پیدا نشد.")
            return

        user_video_formats[chat_id] = {
            "formats": video_formats,
            "url": url
        }

        keyboard = []
        for f in video_formats:
            size_mb = round(f['filesize'] / 1024 / 1024, 2) if f.get('filesize') else '??'
            label = f"{f['height']}p - {size_mb} MB"
            keyboard.append([InlineKeyboardButton(label, callback_data=str(f['format_id']))])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("✅ کیفیت مورد نظر رو انتخاب کن:", reply_markup=reply_markup)

    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    format_id = query.data
    chat_id = query.message.chat_id

    user_data = user_video_formats.get(chat_id)

    if not user_data:
        await query.message.reply_text("❌ اطلاعاتی از لینک قبلی یافت نشد. دوباره لینک رو بفرست.")
        return

    formats = user_data["formats"]
    url = user_data["url"]

    selected_format = next((f for f in formats if str(f['format_id']) == format_id), None)

    if not selected_format:
        await query.message.reply_text("❌ کیفیت انتخابی معتبر نیست.")
        return

    file_name = f"video_{chat_id}.mp4"

    await query.message.reply_text("📥 در حال دانلود ویدیو... لطفاً صبر کن")

    try:
        ydl_opts = {
            'quiet': True,
            'outtmpl': file_name,
            'format': format_id,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        file_size = os.path.getsize(file_name) / 1024 / 1024  # MB

        if file_size < 1990:
            await query.message.reply_text("📤 در حال ارسال ویدیو...")
            with open(file_name, 'rb') as video_file:
                await query.message.reply_document(chat_id=chat_id, document=video_file, caption="✅ دانلود کامل شد!")
        else:
            await query.message.reply_text("🛜 حجم فایل زیاده، در حال آپلود به GoFile.io...")
            upload_url = "https://api.gofile.io/uploadFile"
            with open(file_name, 'rb') as f:
                response = requests.post(upload_url, files={"file": f})
                res_json = response.json()

            if res_json["status"] == "ok":
                file_link = res_json["data"]["downloadPage"]
                await query.message.reply_text(f"✅ آپلود کامل شد. لینک دانلود:\n{file_link}")
            else:
                await query.message.reply_text("❌ خطا در آپلود فایل بزرگ.")

        os.remove(file_name)

    except Exception as e:
        await query.message.reply_text(f"❌ خطا در دانلود یا ارسال: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ ربات در حال اجراست...")
    app.run_polling()

if __name__ == '__main__':
    main()
