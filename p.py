import os
import json
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = "6654800068:AAGNhkRs39HWR6D3B3Iu8yOzJCgbuH7S7sk"  # توکن ربات خود را جایگزین کنید

def extract_video_url(soup):
    script_tags = soup.find_all('script', type='application/ld+json')
    for script in script_tags:
        try:
            data = json.loads(script.string)
            if isinstance(data, list):
                for item in data:
                    if '@type' in item and item['@type'] == 'VideoObject' and 'thumbnailUrl' in item:
                        video_url = item['thumbnailUrl']
                        if video_url.startswith('https://ei.phncdn.com/videos'):
                            return video_url
            else:
                if '@type' in data and data['@type'] == 'VideoObject' and 'thumbnailUrl' in data:
                    video_url = data['thumbnailUrl']
                    if video_url.startswith('https://ei.phncdn.com/videos'):
                        return video_url
        except Exception:
            continue
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! لینک ویدیوی خود را ارسال کنید تا دانلود شود."
    )

async def ask_for_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    context.user_data['video_page_url'] = url

    # بررسی اولیه لینک (اختیاری)
    try:
        response = requests.get(url)
        if response.status_code != 200:
            await update.message.reply_text("خطا: صفحه قابل دسترسی نیست.")
            return
    except Exception:
        await update.message.reply_text("خطا: لینک معتبر نیست یا دسترسی ممکن نیست.")
        return

    keyboard = [
        [
            InlineKeyboardButton("شروع دانلود 🎬", callback_data='download_video'),
            InlineKeyboardButton("لغو ❌", callback_data='cancel'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "لینک دریافت شد. آیا می‌خواهید دانلود را شروع کنید؟",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'download_video':
        url = context.user_data.get('video_page_url')
        if not url:
            await query.edit_message_text("خطا: لینک ویدیویی یافت نشد.")
            return

        msg = await query.edit_message_text("در حال دانلود ویدیو... لطفا صبر کنید.")

        try:
            response = requests.get(url)
            if response.status_code != 200:
                await query.edit_message_text("خطا: صفحه قابل دسترسی نیست.")
                return

            soup = BeautifulSoup(response.content, 'html.parser')
            video_url = extract_video_url(soup)

            if not video_url:
                await query.edit_message_text("خطا: ویدیویی یافت نشد.")
                return

            # دانلود ویدیو
            file_name = "downloaded_video.mp4"
            with requests.get(video_url, stream=True) as video_response:
                total_size = int(video_response.headers.get('content-length', 0))
                if total_size == 0:
                    await query.edit_message_text("خطا: اندازه فایل مشخص نیست.")
                    return

                with open(file_name, 'wb') as f:
                    for chunk in video_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            await query.edit_message_text("دانلود کامل شد. در حال ارسال فایل...")

            with open(file_name, 'rb') as f:
                await context.bot.send_video(chat_id=query.message.chat_id, video=f)

            os.remove(file_name)
            await query.message.delete()
        except Exception as e:
            await query.edit_message_text(f"خطا در دانلود: {e}")

    elif query.data == 'cancel':
        await query.edit_message_text("عملیات دانلود لغو شد.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), ask_for_download))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("ربات در حال اجراست...")
    app.run_polling()
