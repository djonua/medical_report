import logging
import json
import os

def process_file(file_path, chatgpt_api, chatgpt_vision_api, ai_instructions):
    """
    Обрабатывает файл с транскриптом и возвращает результат в формате JSON
    """
    try:
        # Проверяем существование файла
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл {file_path} не найден")
            
        # Читаем содержимое файла
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Получаем ответ от ChatGPT
        response = chatgpt_api.process(ai_instructions, content)
        
        # Проверяем наличие ответа
        if not response or 'choices' not in response:
            raise ValueError("Некорректный ответ от API")
            
        # Извлекаем JSON из ответа
        try:
            result = json.loads(response['choices'][0]['message']['content'])
            return result
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка при разборе JSON: {str(e)}")
            
    except Exception as e:
        logging.error(f"Ошибка при обработке файла: {str(e)}")
        raise
