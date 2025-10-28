import os
import asyncio
import io
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, ApplicationBuilder, CallbackQueryHandler
import speech_recognition 
from pydub import AudioSegment 
from gigachat import GigaChat

giga = GigaChat(
    credentials='MDE5YTI1YzEtZDg1Yy03ZDc3LWJiNmEtZTMzNDE1MzQyNTFhOmVjMjk5YzRlLWE3ZjgtNDc4ZS04ZDk1LWQ5NDBhZDc3NzIyZg==',
    verify_ssl_certs=False
)

(MAIN_MENU, VOICE, TEXT) = range(3)

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
        
        await update.message.reply_text(f"Перевод: {result_text}")
        
    except Exception as e:
        await update.message.reply_text("❌ Ошибка при обращении к AI-модели.")
        print(f"GigaChat error: {e}")

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