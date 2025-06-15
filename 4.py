import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from yt_dlp import YoutubeDL

TOKEN = "6654800068:AAGNhkRs39HWR6D3B3Iu8yOzJCgbuH7S7sk"

ydl_opts = {
    'format': 'bestvideo+bestaudio/best',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'ignoreerrors': True,
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! لینک ویدیو از xnxx یا سایت‌های مشابه رو بفرست، من کیفیت‌ها رو برات می‌فرستم."
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.message.chat.id

    await update.message.reply_text("⏳ در حال استخراج کیفیت‌ها...")

    # استخراج اطلاعات ویدیو با yt-dlp
    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: YoutubeDL({'quiet': True}).extract_info(url, download=False))

        if 'formats' not in info:
            await update.message.reply_text("❌ ویدیو پیدا نشد یا لینک معتبر نیست.")
            return

        formats = info['formats']

        # فیلتر فقط فرمت های mp4 و ویدیو
        video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4']

        if not video_formats:
            await update.message.reply_text("❌ فرمت ویدیویی mp4 قابل دانلود پیدا نشد.")
            return

        # مرتب سازی بر اساس کیفیت (height)
        video_formats = sorted(video_formats, key=lambda x: x.get('height') or 0, reverse=True)

        # ذخیره اطلاعات فرمت‌ها برای دکمه‌ها
        context.user_data['video_formats'] = video_formats

        keyboard = []
        for i, f in enumerate(video_formats[:10]):  # حداکثر 10 کیفیت نمایش میده
            label = f"{f.get('height')}p | {f.get('format_note') or ''} | {f.get('filesize') or 0 // 1024}KB"
            keyboard.append([InlineKeyboardButton(label, callback_data=str(i))])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("کیفیت مورد نظر را انتخاب کن:", reply_markup=reply_markup)

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
    url = format_info.get('url')
    title = format_info.get('format') or "video"
    chat_id = query.message.chat.id

    await query.edit_message_text(f"⏳ در حال دانلود و ارسال ویدیو با کیفیت {format_info.get('height')}p...")

    # ساخت پوشه دانلود اگر وجود ندارد
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    file_path = os.path.join("downloads", f"{title}.mp4".replace(" ", "_"))

    # دانلود ویدیو با yt-dlp در پس زمینه
    ydl_opts_local = {
        'format': format_info.get('format_id'),
        'outtmpl': file_path,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }

    def download_video():
        with YoutubeDL(ydl_opts_local) as ydl:
            ydl.download([format_info['url']])

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, download_video)

    # ارسال ویدیو
    try:
        with open(file_path, 'rb') as video_file:
            await context.bot.send_video(chat_id=chat_id, video=video_file)
        await context.bot.send_message(chat_id=chat_id, text="✅ ویدیو با موفقیت ارسال شد.")
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ خطا در ارسال ویدیو:\n{e}")
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

