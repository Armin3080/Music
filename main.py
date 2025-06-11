from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from bs4 import BeautifulSoup
import requests
import json
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Replace with your Telegram bot token
TOKEN = "6654800068:AAGNhkRs39HWR6D3B3Iu8yOzJCgbuH7S7sk"

def start(update: Update, context: CallbackContext) -> None:
    context.bot.send_message(chat_id=update.effective_chat.id, text='سلام! برای دانلود ویدیو، لینک ویدیو را برای من بفرستید.')

def download_video(update: Update, context: CallbackContext) -> None:
    message = update.message
    chat_id = message.chat_id
    url = message.text.strip()

    if url.startswith('http'):
        response = get_request_with_retry(url)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            video_url = extract_video_url(soup)

            if video_url:
                # Download and send the video
                send_video_from_url(chat_id, video_url, context)
            else:
                context.bot.send_message(chat_id=chat_id, text='ویدیویی یافت نشد.')
        else:
            context.bot.send_message(chat_id=chat_id, text='صفحه قابل دسترسی نیست.')
    else:
        context.bot.send_message(chat_id=chat_id, text='لطفاً لینک ویدیو را بفرستید.')

def extract_video_url(soup):
    script_tags = soup.find_all('script', type='application/ld+json')
    for script in script_tags:
        try:
            data = json.loads(script.string)
            if '@type' in data and data['@type'] == 'VideoObject' and 'contentUrl' in data:
                video_url = data['contentUrl']
                if video_url.startswith('https://cdn77-vid-mp4.xnxx-cdn.com'):
                    return video_url
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            continue
    return None

def send_video_from_url(chat_id, video_url, context):
    file_name = "video.mp4"
    try:
        # Download the video
        video_response = get_request_with_retry(video_url, stream=True)
        if video_response.status_code == 200:
            with open(file_name, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=1024):
                    f.write(chunk)

            # Send the downloaded video to the user
            with open(file_name, 'rb') as video_file:
                context.bot.send_video(chat_id=chat_id, video=video_file, timeout=120)

            # Inform the user
            context.bot.send_message(chat_id=chat_id, text='ویدیو با موفقیت دانلود و ارسال شد.')
        else:
            context.bot.send_message(chat_id=chat_id, text='مشکلی در دانلود ویدیو پیش آمده است.')
    except Exception as e:
        print(f"Error sending video: {e}")
        context.bot.send_message(chat_id=chat_id, text='مشکلی در ارسال ویدیو به وجود آمده است.')
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)

def get_request_with_retry(url, stream=False):
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[ 502, 503, 504 ])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session.get(url, timeout=30, stream=stream)

def error(update: Update, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    print(f"Update {update} caused error: {context.error}")

def main() -> None:
    updater = Updater(TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    # Handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, download_video))

    # Error handler
    dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()
    print("Bot is polling...")
    updater.idle()

if __name__ == '__main__':
    main()
