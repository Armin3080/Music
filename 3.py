import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from yt_dlp import YoutubeDL

TOKEN = "6654800068:AAGNhkRs39HWR6D3B3Iu8yOzJCgbuH7S7sk"
CHANNEL_ID = "@dxdpo"  # نام کاربری یا آیدی عددی کانال

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! لینک ویدیو رو بفرست تا کیفیت‌ها رو برات بیارم.")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    await update.message.reply_text("⏳ در حال استخراج کیفیت‌ها...")

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, lambda: YoutubeDL({'quiet': True}).extract_info(url, download=False))

        if 'formats' not in info:
            await update.message.reply_text("❌ ویدیو پیدا نشد یا لینک معتبر نیست.")
            return

        formats = info['formats']

        # فقط فرمت‌هایی که کدک ویدیو و صدا دارند
        valid_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none']

        # مرتب سازی کیفیت‌ها (بر اساس ارتفاع تصویر)
        valid_formats = sorted(valid_formats, key=lambda x: x.get('height') or 0, reverse=True)

        context.user_data['video_info'] = info
        context.user_data['video_formats'] = valid_formats

        keyboard = []
        for i, f in enumerate(valid_formats[:10]):  # حداکثر ۱۰ کیفیت
            label = f"{f.get('height', 'unknown')}p - {f.get('format_note', '')} - {f.get('format_id')}"
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
    video_info = context.user_data.get('video_info', {})

    if not video_formats or selected_index >= len(video_formats):
        await query.edit_message_text("❌ کیفیت انتخاب شده معتبر نیست.")
        return

    format_info = video_formats[selected_index]
    format_id = format_info.get('format_id')
    url = video_info.get('webpage_url')

    await query.edit_message_text(f"⏳ در حال دانلود و ارسال ویدیو با کیفیت {format_info.get('height')}p به کانال...")

    # پوشه دانلود
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    safe_title = "".join(c if c.isalnum() else "_" for c in video_info.get('title', 'video'))
    file_path = os.path.join("downloads", f"{safe_title}_{format_info.get('height', 'unknown')}p.mp4")

    ydl_opts = {
        'quiet': True,
        'format': format_id,
        'outtmpl': file_path,
        'noplaylist': True,
        'no_warnings': True,
    }

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: YoutubeDL(ydl_opts).download([url]))

        with open(file_path, 'rb') as video_file:
            await context.bot.send_video(chat_id=CHANNEL_ID, video=video_file)

        # پیام موفقیت به کاربر
        await context.bot.send_message(chat_id=query.message.chat.id, text="✅ ویدیو با موفقیت به کانال ارسال شد.")

    except Exception as e:
        await context.bot.send_message(chat_id=query.message.chat.id, text=f"❌ خطا در دانلود یا ارسال ویدیو:\n{e}")

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
