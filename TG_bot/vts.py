from pydub import AudioSegment 
import speech_recognition 
import io

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