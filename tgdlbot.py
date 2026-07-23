import os
import tempfile
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# تنظیمات لاگ برای دیباگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(name)

# دیکشنری زبان‌ها
LANGUAGES = {
    'fa': {
        'welcome': 'سلام! 👋\nلطفاً لینک ویدیو (یوتیوب، اینستاگرام، تیک‌تاک و...) را ارسال کنید تا آن را برایتان دانلود کنم.',
        'lang_set': '✅ زبان با موفقیت روی فارسی تنظیم شد.',
        'downloading': '⏳ در حال دانلود... لطفاً صبر کنید.',
        'error': '❌ خطا در دانلود. لطفاً لینک را بررسی کنید یا مطمئن شوید ویدیو عمومی است.',
        'too_large': '⚠️ حجم فایل بیشتر از ۵۰ مگابایت است و تلگرام اجازه ارسال آن را نمی‌دهد.',
        'choose_lang': '🌐 لطفاً زبان خود را انتخاب کنید / Choose your language:'
    },
    'en': {
        'welcome': 'Hello! 👋\nPlease send a video link (YouTube, Instagram, TikTok, etc.) to download it.',
        'lang_set': '✅ Language set to English successfully.',
        'downloading': '⏳ Downloading... Please wait.',
        'error': '❌ Error downloading. Please check the link or ensure the video is public.',
        'too_large': '⚠️ File size exceeds 50MB. Telegram does not allow sending it.',
        'choose_lang': '🌐 لطفاً زبان خود را انتخاب کنید / Choose your language:'
    }
}

# ذخیره موقت زبان کاربران (در یک پروژه واقعی از دیتابیس استفاده کنید)
user_data = {}

def get_text(user_id, key):
    lang = user_data.get(user_id, 'en')
    return LANGUAGES[lang][key]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("فارسی 🇮🇷", callback_data='lang_fa'),
         InlineKeyboardButton("English 🇬🇧", callback_data='lang_en')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(LANGUAGES['en']['choose_lang'], reply_markup=reply_markup)

async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    lang = query.data.split('_')[1]
    user_data[user_id] = lang
    
    await query.edit_message_text(text=get_text(user_id, 'lang_set') + "\n\n" + get_text(user_id, 'welcome'))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text.strip()
    
    # بررسی ساده اینکه آیا متن یک لینک است یا خیر
    if not url.startswith('http'):
        await update.message.reply_text(get_text(user_id, 'error'))
        return

    await update.message.reply_text(get_text(user_id, 'downloading'))

    # استفاده از TemporaryDirectory برای پاکسازی خودکار فایل‌ها پس از اتمام کار
    with tempfile.TemporaryDirectory() as tmpdirname:
        ydl_opts = {
    'outtmpl': os.path.join(tmpdirname, '%(id)s.%(ext)s'),
    'format': 'best[ext=mp4]/best',
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'merge_output_format': 'mp4',
}
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # اگر فرمت نهایی mp4 باشد، پسوند ممکن است تغییر کند
                base_name = os.path.splitext(filename)[0]
                final_file = base_name + '.mp4'
                
                if not os.path.exists(final_file):
                    # اگر فایل با پسوند mp4 پیدا نشد، اولین فایل موجود را برمی‌داریم
                    files = os.listdir(tmpdirname)
                    if files:
                        final_file = os.path.join(tmpdirname, files[0])
                    else:
                        raise Exception("File not found")
                      # بررسی محدودیت ۵۰ مگابایتی تلگرام
                file_size = os.path.getsize(final_file)
                if file_size > 50 * 1024 * 1024:
                    await update.message.reply_text(get_text(user_id, 'too_large'))
                    return

                             # ارسال ویدیو
                with open(final_file, 'rb') as video_file:
                    print("Uploading:", final_file, os.path.getsize(final_file))
                    await update.message.reply_video(
                        video=video_file,
                        supports_streaming=True
                    )

        except Exception:
            logger.exception("Download error")
            await update.message.reply_text(get_text(user_id, 'error'))

def main():
    # توکن ربات خود را اینجا وارد کنید
    TOKEN = "Token-Here"

    from telegram.request import HTTPXRequest

    request = HTTPXRequest(
    connect_timeout=120,
    read_timeout=300,
    write_timeout=300,
    pool_timeout=120
)

    application = Application.builder()\
        .token(TOKEN)\
        .request(request)\
        .build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(lang_callback, pattern="^lang_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running... Press Ctrl+C to stop.")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if name == 'main':
    main()
