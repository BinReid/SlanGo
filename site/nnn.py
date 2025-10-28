import speech_recognition 
from pydub import AudioSegment 
import io
from gigachat import GigaChat
# Инициализация GigaChat
giga = GigaChat(
    credentials='MDE5YTI1YzEtZDg1Yy03ZDc3LWJiNmEtZTMzNDE1MzQyNTFhOmVjMjk5YzRlLWE3ZjgtNDc4ZS04ZDk1LWQ5NDBhZDc3NzIyZg==',
    verify_ssl_certs=False
)

def process_with_gigachat(text: str):
    """Функция обработки текста через GigaChat"""
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
        return result_text
        
    except Exception as e:
        print(f"GigaChat error: {e}")
        return None

def ogg_to_wav_in_memory(ogg_data):
    """Конвертирует OGG в WAV в памяти"""
    try:
        ogg_buffer = io.BytesIO(ogg_data)
        audio = AudioSegment.from_file(ogg_buffer, format="ogg")
        
        wav_buffer = io.BytesIO()
        audio.export(wav_buffer, format="wav")
        wav_buffer.seek(0)
        
        return wav_buffer
    except Exception as e:
        print(f"Audio conversion error: {e}")
        return None

def recognize_speech_from_memory(audio_data):
    """Распознает речь из аудиоданных"""
    try:
        # Создаем временный файл для отладки
        with open('debug_audio.webm', 'wb') as f:
            f.write(audio_data)
        print(f"Audio data size: {len(audio_data)} bytes")
        
        # Пробуем разные форматы
        try:
            # Пытаемся прочитать как WebM/Opus
            audio = AudioSegment.from_file(io.BytesIO(audio_data), format="webm")
        except:
            try:
                # Пытаемся прочитать как OGG
                audio = AudioSegment.from_file(io.BytesIO(audio_data), format="ogg")
            except:
                try:
                    # Пытаемся прочитать как MP4
                    audio = AudioSegment.from_file(io.BytesIO(audio_data), format="mp4")
                except Exception as e:
                    raise Exception(f"Не поддерживаемый формат аудио: {e}")
        
        # Конвертируем в WAV
        wav_buffer = io.BytesIO()
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(wav_buffer, format="wav")
        wav_buffer.seek(0)
        
        # Распознаем речь
        recognizer = speech_recognition.Recognizer()
        
        with speech_recognition.WavFile(wav_buffer) as source:
            # Уменьшаем фоновый шум
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            wav_audio = recognizer.record(source)
        
        text = recognizer.recognize_google(wav_audio, language='ru')
        print(f"Recognized text: {text}")
        return text
        
    except speech_recognition.UnknownValueError:
        raise Exception("Не удалось распознать речь. Попробуйте говорить четче и громче.")
    except speech_recognition.RequestError as e:
        raise Exception(f"Ошибка сервиса распознавания: {e}")
    except Exception as e:
        print(f"Audio processing error: {e}")
        raise Exception(f"Ошибка при обработке аудио: {e}")