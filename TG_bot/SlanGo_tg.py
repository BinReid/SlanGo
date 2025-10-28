import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, ApplicationBuilder, CallbackQueryHandler
import speech_recognition 
from nn import process_with_gigachat
from vts import download_file_to_memory, recognize_speech_from_memory

(MAIN_MENU, VOICE, TEXT) = range(3)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎤 Записать голосовое сообщение", callback_data="voice")],
        [InlineKeyboardButton("📝 Написать текстовое сообщение", callback_data="text")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=reply_markup)
    
    return MAIN_MENU

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == 'voice':
        await query.edit_message_text("🎤 Запишите ваше голосовое сообщение")
        return VOICE

    elif query.data == 'text':
        await query.edit_message_text("📝 Напишите ваше предложение")
        return TEXT

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🔍 Обрабатываю голосовое сообщение...")
        
        voice = update.message.voice
        ogg_data = await download_file_to_memory(context.bot, voice.file_id)
        
        text = await asyncio.get_event_loop().run_in_executor(
            None, 
            recognize_speech_from_memory, 
            ogg_data
        )
                
        await process_with_gigachat(update, text)
        
        keyboard = [
            [InlineKeyboardButton("🎤 Записать голосовое сообщение", callback_data="voice")],
            [InlineKeyboardButton("📝 Написать текстовое сообщение", callback_data="text")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите следующее действие:", reply_markup=reply_markup)
        return MAIN_MENU
        
    except speech_recognition.UnknownValueError:
        await update.message.reply_text("❌ Не удалось распознать речь. Попробуйте записать сообщение четче.")
        return await return_to_input_choice(update)
    except speech_recognition.RequestError as e:
        await update.message.reply_text(f"❌ Ошибка сервиса распознавания")
        return await return_to_input_choice(update)
    except Exception as e:
        await update.message.reply_text("❌ Произошла ошибка при обработке голосового сообщения.")
        print(f"Error: {e}")
        return await return_to_input_choice(update)
    
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🔍 Обрабатываю сообщение...")
        text = update.message.text
                
        await process_with_gigachat(update, text)
        
        keyboard = [
            [InlineKeyboardButton("🎤 Записать голосовое сообщение", callback_data="voice")],
            [InlineKeyboardButton("📝 Написать текстовое сообщение", callback_data="text")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Выберите следующее действие:", reply_markup=reply_markup)
        return MAIN_MENU
        
    except Exception as e:
        await update.message.reply_text("❌ Произошла ошибка при обработке сообщения.")
        print(f"Error: {e}")
        return await return_to_input_choice(update)


async def return_to_input_choice(update: Update):
    keyboard = [
        [InlineKeyboardButton("🎤 Записать голосовое сообщение", callback_data="voice")],
        [InlineKeyboardButton("📝 Написать текстовое сообщение", callback_data="text")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите способ ввода:", reply_markup=reply_markup)
    return MAIN_MENU

async def unsupported_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Этот тип сообщений не поддерживается. Пожалуйста, используйте только текст или голосовые сообщения.")
    return await return_to_input_choice(update)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Exception while handling an update: {context.error}")

def main():
    app = ApplicationBuilder().token("8381057494:AAF7QAAZVgQF31pMMUIY18NfvyTDB0yKAk0").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(main_menu_handler, pattern='^(voice|text)$'),
                MessageHandler(filters.ALL, unsupported_message_handler)
            ],
            VOICE: [
                MessageHandler(filters.VOICE, voice_handler),
                MessageHandler(filters.ALL, unsupported_message_handler)
            ],
            TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler),
                MessageHandler(filters.ALL, unsupported_message_handler)
            ]
        },
        fallbacks=[CommandHandler('start', start_command)],
    )

    app.add_handler(conv_handler)
    app.add_error_handler(error_handler)
    
    print("Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()