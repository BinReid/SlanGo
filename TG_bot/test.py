import requests
import os

# Ваш API ключ от Hugging Face
API_TOKEN = "d567d7e802e84e8dad371c3dbdaac497"
API_URL = "https://api-inference.huggingface.co/models/Mungert/Meta-Llama-3-8B-Instruct-GGUF"  # + id модели
headers = {"Authorization": f"Bearer {API_TOKEN}"}

def query_hf_api(model_id, payload):
    """
    Универсальная функция для запроса к Hugging Face Inference API
    """
    response = requests.post(API_URL + model_id, headers=headers, json=payload)
    return response.json()

# Пример 1: Анализ тональности
model_id = "cardiffnlp/twitter-roberta-base-sentiment-latest"
payload = {"inputs": "I love this product! It's amazing."}
output = query_hf_api(model_id, payload)
print(output)
# [{'label': 'positive', 'score': 0.98}]

# Пример 2: Суммаризация текста
model_id = "Falconsai/text_summarization"
payload = {"inputs": "Длинный текст, который нужно сократить...", "parameters": {"max_length": 100}}
output = query_hf_api(model_id, payload)
print(output)
# [{'summary_text': 'Сокращенный текст...'}]

# Пример 3: Получение эмбеддингов
model_id = "sentence-transformers/all-MiniLM-L6-v2"
payload = {"inputs": "The weather is beautiful today."}
output = query_hf_api(model_id, payload)
print(len(output[0]))  # Длина вектора эмбеддинга
# 384