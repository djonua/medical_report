class Doctor:
    # Словарь соответствия специализаций
    SPECIALIZATIONS = {
        "Педиатр": "pediatrician",
        "Терапевт": "general_physician",
        "Невролог": "neurologist",
        "Кардиолог": "cardiologist",
        "Офтальмолог": "ophthalmologist",
        "Отоларинголог": "otolaryngologist",
        "Хирург": "surgeon",
        "Гинеколог": "gynecologist",
        "Уролог": "urologist",
        "Эндокринолог": "endocrinologist"
    }
    
    # Обратный словарь для получения русского названия
    SPECIALIZATIONS_REVERSE = {v: k for k, v in SPECIALIZATIONS.items()}
    
    def __init__(self, name, specialization_code):
        self.name = name
        self.specialization_code = specialization_code
    
    @property
    def specialization_name(self):
        """Получить русское название специализации"""
        return self.SPECIALIZATIONS_REVERSE.get(self.specialization_code, self.specialization_code)
    
    def to_dict(self):
        """Преобразовать в словарь для JSON"""
        return {
            'name': self.name,
            'specialization': self.specialization_name
        }
    
    @classmethod
    def from_dict(cls, data):
        """Создать объект из словаря"""
        name = data.get('name')
        specialization = data.get('specialization')
        if name and specialization:
            # Получаем код специализации из русского названия
            specialization_code = cls.SPECIALIZATIONS.get(specialization)
            if specialization_code:
                return cls(name, specialization_code)
        return None 