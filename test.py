import os
import asyncio
import io
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, ApplicationBuilder
import speech_recognition 
from pydub import AudioSegment 
from gigachat import GigaChat

giga = GigaChat(
    credentials='MDE5YTI1YzEtZDg1Yy03ZDc3LWJiNmEtZTMzNDE1MzQyNTFhOmVjMjk5YzRlLWE3ZjgtNDc4ZS04ZDk1LWQ5NDBhZDc3NzIyZg==',
    verify_ssl_certs=False
)

(MAIN_MENU, VOICE, TEXT, SLOVO) = range(4)

def ogg_to_wav_in_memory(ogg_data):
    ogg_buffer = io.BytesIO(ogg_data)
    audio = AudioSegment.from_file(ogg_buffer, format="ogg")
    
    wav_buffer = io.BytesIO()
    audio.export(wav_buffer, format="wav")
    wav_buffer.seek(0)
    
    return wav_buffer

def recognize_speech_from_memory(ogg_data):
    try:
        wav_buffer = ogg_to_wav_in_memory(ogg_data)
        recognizer = speech_recognition.Recognizer()
        
        with speech_recognition.WavFile(wav_buffer) as source:
            wav_audio = recognizer.record(source)
        
        text = recognizer.recognize_google(wav_audio, language='ru')
        return text
        
    except Exception as e:
        raise e

async def download_file_to_memory(bot, file_id):
    file = await bot.get_file(file_id)
    file_content = await file.download_as_bytearray()
    return file_content

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [['Словарь', 'Записать голосовое сообщение/написать предложение']]
    await update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return MAIN_MENU

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == 'Словарь':
        await update.message.reply_text("Напшите слово, которое желаете понять")
        return SLOVO

    elif text == 'Записать голосовое сообщение/написать предложение':
        reply_keyboard = [['Голосовое сообщение', 'Текстовое сообщение'], ['Назад']]
        await update.message.reply_text(
            "Выберите способ ввода:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return VOICE

    else:
        await update.message.reply_text("Пожалуйста, выберите действие из списка.")
        return MAIN_MENU

async def voice_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == 'Голосовое сообщение':
        await update.message.reply_text("🎤 Запишите ваше голосовое сообщение...")
        return VOICE

    elif text == 'Текстовое сообщение':
        await update.message.reply_text("📝 Напишите ваше предложение...")
        return TEXT

    elif text == 'Назад':
        reply_keyboard = [['Словарь', 'Записать голосовое сообщение/написать предложение']]
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return MAIN_MENU

    else:
        await update.message.reply_text("Пожалуйста, выберите способ ввода из списка.")
        return VOICE

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
        
        reply_keyboard = [['Словарь', 'Записать голосовое сообщение/написать предложение']]
        await update.message.reply_text(
            "Выберите следующее действие:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
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
        user_text = update.message.text
        await update.message.reply_text("🔍 Обрабатываю текстовое сообщение...")
        
        await process_with_gigachat(update, user_text)
        
        reply_keyboard = [['Словарь', 'Записать голосовое сообщение/написать предложение']]
        await update.message.reply_text(
            "Выберите следующее действие:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return MAIN_MENU
        
    except Exception as e:
        await update.message.reply_text("❌ Произошла ошибка при обработке текстового сообщения.")
        print(f"Error: {e}")
        return await return_to_input_choice(update)

async def process_with_gigachat(update: Update, text: str):
    try:
        prompt = f"""Ты — специализированный переводчик между русским литературным языком и современным русским сленгом. Твоя задача — точно и лаконично преобразовывать предложения между этими двумя регистрами.

**Ключевые правила:**

1. **Автоопределение:** Ты должен САМОСТОЯТЕЛЬНО определять, является ли исходное предложение сленгом или литературной речью. Не спрашивай пользователя уточнений.
2. **Точность:** Сохраняй исходный смысл, интонацию и контекст. Не добавляй от себя пояснений, комментариев или эмоций, которых не было в исходнике.
3. **Лаконичность:** Твой ответ — это ТОЛЬКО преобразованное предложение. Никаких лишних фраз вроде «Перевод:» или «Это значит:».
4. **Естественность:** Преобразованное предложение должно звучать естественно для целевого регистра (сленг или литературный язык).

**Алгоритм твоих действий:**

* **Если в запросе есть сленг (например, "краш", "чилить", "рофл", "кринж", "агриться")** -> преобразуй его в грамотное, нейтральное предложение на литературном русском.
* **Если в запросе строгая литературная речь** -> преобразуй его в естественное предложение со сленгом, подбирая уместные современные эквиваленты.
* **Если в запросе смесь сленга и нейтральной речи** -> определи преобладающий стиль и преобразуй всё предложение в противоположный регистр.

**Примеры для обучения:**

* Вход: "Вчера видел своего краша, такой кринжовый вид был."
  Выход: "Вчера я видел человека, который мне нравится, у него был очень нелепый вид."

* Вход: "Мой начальник сегодня очень раздоров и всех критикует."
  Выход: "Мой босс сегодня сильно агрится и всех рофлит."

* Вход: "Не хочу сегодня заниматься серьезными делами, просто отдохну."
  Выход: "Не хочу сегодня париться, просто почилю."

* Вход: "Этот человек ведет себя очень глупо и вызывающе."
  Выход: "Этот тип ведет себя по-крайне кринжово и на понтах."

**Исходный текст для преобразования:** {text}"""

        response = giga.chat(prompt)
        result_text = response.choices[0].message.content
        
        await update.message.reply_text(f"{result_text}")
        
    except Exception as e:
        await update.message.reply_text("❌ Ошибка при обращении к AI-модели.")
        print(f"GigaChat error")

async def return_to_input_choice(update: Update):
    reply_keyboard = [['Голосовое сообщение', 'Текстовое сообщение'], ['Назад']]
    await update.message.reply_text(
        "Выберите способ ввода:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return VOICE

async def unsupported_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Этот тип сообщений не поддерживается. Пожалуйста, используйте только текст или голосовые сообщения.")
    
    if update.message.text:
        reply_keyboard = [['Словарь', 'Записать голосовое сообщение/написать предложение']]
        await update.message.reply_text(
            "Выберите действие из меню:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return MAIN_MENU
    else:
        return await return_to_input_choice(update)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Exception while handling an update: {context.error}")

def main():
    app = ApplicationBuilder().token("8381057494:AAF7QAAZVgQF31pMMUIY18NfvyTDB0yKAk0").build()

    allowed_messages = filters.TEXT | filters.VOICE
    
    forbidden_messages = filters.ALL & (~allowed_messages)
    
    def menu_text_filter(message):
        if not message.text:
            return False
        return message.text not in ['Словарь', 'Записать голосовое сообщение/написать предложение', 
                                   'Голосовое сообщение', 'Текстовое сообщение', 'Назад']

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler),
                MessageHandler(forbidden_messages, unsupported_message_handler)
            ],
            VOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, voice_choice_handler),
                MessageHandler(filters.VOICE, voice_handler),
                MessageHandler(forbidden_messages, unsupported_message_handler)
            ],
            TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler),
                MessageHandler(forbidden_messages, unsupported_message_handler)
            ]
        },
        fallbacks=[CommandHandler('start', start_command)],
    )

    app.add_handler(conv_handler)
    
    app.add_handler(MessageHandler(forbidden_messages, unsupported_message_handler))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'^(?!(Словарь|Записать голосовое сообщение/написать предложение|Голосовое сообщение|Текстовое сообщение|Назад)$)'), 
                                 unsupported_message_handler))
    
    app.add_error_handler(error_handler)
    
    print("Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()