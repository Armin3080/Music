import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from yt_dlp import YoutubeDL

TOKEN = "6654800068:AAGNhkRs39HWR6D3B3Iu8yOzJCgbuH7S7sk"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! لینک ویدیو رو بفرست تا کیفیت‌ها رو برات بیارم."
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.message.chat.id

    await update.message.reply_text("⏳ در حال استخراج کیفیت‌ها...")

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: YoutubeDL({'quiet': True}).extract_info(url, download=False))

        if 'formats' not in info:
            await update.message.reply_text("❌ ویدیو پیدا نشد یا لینک معتبر نیست.")
            return

        formats = info['formats']

        # فقط فرمت‌هایی که URL مستقیم دارن (یعنی قابلیت دانلود مستقیم)
        valid_formats = [f for f in formats if f.get('url') and not f.get('is_live')]

        # فقط فرمت‌هایی که کدک ویدیو دارند
        valid_formats = [f for f in valid_formats if f.get('vcodec') != 'none']

        if not valid_formats:
            await update.message.reply_text("❌ فرمت دانلود شدنی یافت نشد.")
            return

        # مرتب سازی کیفیت‌ها (بر اساس ارتفاع تصویر)
        valid_formats = sorted(valid_formats, key=lambda x: x.get('height') or 0, reverse=True)

        context.user_data['video_formats'] = valid_formats

        keyboard = []
        for i, f in enumerate(valid_formats[:10]):  # حداکثر 10 کیفیت نمایش داده می‌شود
            size_mb = (f.get('filesize') or 0) / (1024 * 1024)
            label = f"{f.get('height')}p - {f.get('format_note', '')} - {size_mb:.1f}MB"
            keyboard.append([InlineKeyboardButton(label, callback_data=str(i))])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("لطفا کیفیت مورد نظر را انتخاب کن:", reply_markup=reply_markup)

    except Exception as e:
        await update.message.reply_text(f"❌ خطا در پردازش لینک:\n{e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_index = int(query.data)
    video_formats = context.user_data.get('video_formats', [])

    if not video_formats or selected_index >= len(video_formats):
        await query.edit_message_text("❌ کیفیت انتخاب شده معتبر نیست.")
        return

    format_info = video_formats[selected_index]
    video_url = format_info.get('url')
    title = format_info.get('format') or "video"
    chat_id = query.message.chat.id

    await query.edit_message_text(f"⏳ در حال دانلود و ارسال ویدیو با کیفیت {format_info.get('height')}p...")

    # ساخت پوشه دانلود در صورت نیاز
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    # نام فایل بر اساس عنوان ویدیو
    file_path = os.path.join("downloads", f"{title}_{format_info.get('height', 'unknown')}p.mp4".replace(" ", "_"))

    try:
        # دانلود فایل مستقیم (بدون yt-dlp اینجا)
        import requests
        with requests.get(video_url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        # ارسال ویدیو
        with open(file_path, 'rb') as video_file:
            await context.bot.send_video(chat_id=chat_id, video=video_file)
        await context.bot.send_message(chat_id=chat_id, text="✅ ویدیو با موفقیت ارسال شد.")

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ خطا در دانلود یا ارسال ویدیو:\n{e}")

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("ربات اجرا شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
