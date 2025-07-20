import os

def get_config():
    return {
        'SECRET_KEY': os.environ.get('SECRET_KEY'),
        'MONGO_URI': os.environ.get('MONGO_URI'),
        'FERNET_KEY': os.environ.get('FERNET_KEY'),
        'OCR_KEY': os.environ.get('OCR_KEY'),
        'SESSION_TYPE': 'filesystem'
    }
