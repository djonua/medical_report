import process_utils

ai_instructions = '''
Вот записанный и распознанный разговор между неврологом и пациентом. Там допустимы ошибки. Твоя задача из этого разговора извлечь необходимые данные для составления заключения. 
Ответ необходимо записать в формате JSON.
Вот пример заполненного заключения:

{
  "patient": {
    "name": "Имя пациента",
    "age": "Возраст пациента"
  },
  "complaints": [
    "Описание жалоб пациента"
  ],
  "provisional diagnosis": [
    "Предварительный диагноз"
  ],
  "recommendations": [
    "Рекомендации врача"
  ]
}

Тут будут специализированные инструкции для невролога.
'''

def process_file(file_path, chatgpt_api, chatgpt_vision_api):
    return process_utils.process_file(file_path, chatgpt_api, chatgpt_vision_api, ai_instructions) 