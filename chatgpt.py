import requests
from openai import OpenAI
import os
import logging


class ChatGPTAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)

    def get_response(self, messages):
        response = self.client.chat.completions.create(
            model="gpt-4o-2024-08-06",  # Используем актуальную модель
            messages=messages,
            temperature=0.01,
            response_format={"type": "json_object"}
        )
        return response

    def process(self, ai_instructions, content=None, file_path=None):
        logging.info(f"Обработка файла: {file_path}")
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            messages = []
            messages.append({'role': 'system', 'content': ai_instructions})

            if content:
                messages.append({'role': 'user', 'content': content})

            if file_path:
                file_extension = os.path.splitext(file_path)[1].lower()
                if file_extension == ".txt":
                    with open(file_path, 'r', encoding='utf-8') as file:
                        content = file.read()   
                messages.append({'role': 'user', 'content': content})

            logging.info(messages)

            payload = {
                "model": "gpt-4o-2024-08-06",
                "messages": messages,
                "temperature": 0.01,
                "response_format": {"type": "json_object"},
                "max_tokens": 8000,
            }

            logging.info("Отправка запроса в OpenAI API.")
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            logging.info("Запрос успешно выполнен.")
            logging.info(response.json())
            return response.json()

        except requests.RequestException as e:
            logging.error(f"Ошибка при запросе к OpenAI API: {e}")
            raise
        except Exception as e:
            logging.error(f"Неожиданная ошибка: {e}")
            raise
