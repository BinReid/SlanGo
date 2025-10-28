from flask import render_template, request, jsonify, Blueprint
import socket
from nnn import process_with_gigachat, recognize_speech_from_memory

main_bp = Blueprint('main', __name__)
    
def get_local_ip():
    """Получает локальный IP адрес компьютера"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_bot_info():
    """Функция для получения информации о боте"""
    local_ip = get_local_ip()
    port = 5000
    
    return {
        'name': 'SLANGO',
        'description': 'Мост между сленгом и литературной речью',
        'features': [
            'Автоматический перевод сленга на литературный язык',
            'Обширная база современных выражений',
            'Обратный перевод - из литературного в сленг',
            'Примеры использования в контексте'
        ],
        'telegram_url': 'https://t.me/Slan_Go_bot',
        'web_version_url': '/webot',
        'slovar': '/slovar',
        'local_ip': local_ip,
        'port': port,
        'local_url': f'http://{local_ip}:{port}'
    }

@main_bp.route('/')
def index():
    bot_info = get_bot_info()
    return render_template('visit.html', bot_info=bot_info)

@main_bp.route('/webot')
def webot():
    bot_info = get_bot_info()
    return render_template('visitka.html', bot_info=bot_info)

@main_bp.route('/slovar')
def slovar():
    bot_info = get_bot_info()
    return render_template('slovar.html', bot_info=bot_info)

@main_bp.route('/translate/text', methods=['POST'])
def translate_text():
    """Обработка текстового перевода"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'success': False, 'error': 'Текст не может быть пустым'})
        
        result = process_with_gigachat(text)
        
        if result:
            return jsonify({
                'success': True,
                'original_text': text,
                'translated_text': result
            })
        else:
            return jsonify({'success': False, 'error': 'Ошибка при обработке текста'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@main_bp.route('/translate/voice', methods=['POST'])
def translate_voice():
    """Обработка голосового перевода"""
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'Аудио файл не найден'})
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'success': False, 'error': 'Файл не выбран'})
        
        # Читаем аудио данные
        audio_data = audio_file.read()
        
        if len(audio_data) < 100:
            return jsonify({'success': False, 'error': 'Аудио файл слишком короткий'})
        
        # Распознаем речь
        recognized_text = recognize_speech_from_memory(audio_data)
        
        if not recognized_text:
            return jsonify({'success': False, 'error': 'Не удалось распознать речь'})
        
        # Переводим через GigaChat
        result = process_with_gigachat(recognized_text)
        
        if result:
            return jsonify({
                'success': True,
                'recognized_text': recognized_text,
                'translated_text': result
            })
        else:
            return jsonify({'success': False, 'error': 'Ошибка при переводе распознанного текста'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})