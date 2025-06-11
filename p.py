import os
import json
import requests
from bs4 import BeautifulSoup
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

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
    await update.message.reply_text("سلام! لینک ویدیوی خود را ارسال کنید تا دانلود شود.")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    msg = await update.message.reply_text("در حال بررسی لینک...")

    try:
        response = requests.get(url)
        if response.status_code != 200:
            await msg.edit_text("خطا: صفحه قابل دسترسی نیست.")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        video_url = extract_video_url(soup)

        if not video_url:
            await msg.edit_text("خطا: ویدیویی یافت نشد.")
            return

        await msg.edit_text("لینک ویدیو پیدا شد. در حال دانلود...")

        # دانلود ویدیو
        file_name = "downloaded_video.mp4"
        with requests.get(video_url, stream=True) as video_response:
            total_size = int(video_response.headers.get('content-length', 0))
            if total_size == 0:
                await msg.edit_text("خطا: اندازه فایل مشخص نیست.")
                return

            downloaded_size = 0
            with open(file_name, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

        await msg.edit_text("دانلود کامل شد. در حال ارسال فایل...")

        # ارسال فایل به کاربر
        with open(file_name, 'rb') as f:
            await update.message.reply_video(video=f, timeout=120)

        os.remove(file_name)
        await msg.delete()
    except Exception as e:
        await update.message.reply_text(f"خطا در دانلود: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_video))

    print("ربات در حال اجراست...")
    app.run_polling()
