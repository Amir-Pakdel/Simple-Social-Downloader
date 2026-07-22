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
