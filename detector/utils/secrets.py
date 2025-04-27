import os
import base64
from cryptography.fernet import Fernet
from django.core.management.utils import get_random_secret_key

def generate_key():
    """Generate a new Fernet key for encryption"""
    return Fernet.generate_key()

def generate_secret_key():
    """Generate a new Django secret key"""
    return get_random_secret_key()

def save_secret_key(secret_key, key_file):
    """Save secret key to file"""
    with open(key_file, 'w') as f:
        f.write(secret_key)

def load_secret_key(key_file):
    """Load secret key from file"""
    try:
        with open(key_file) as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def get_or_create_secret_key(key_file):
    """Get existing Django secret key or create a new one"""
    try:
        with open(key_file) as f:
            secret_key = f.read().strip()
    except FileNotFoundError:
        secret_key = get_random_secret_key()
        with open(key_file, 'w') as f:
            f.write(secret_key)
    return secret_key

def get_or_create_fernet_key(key_file):
    """Get existing Fernet key or create a new one"""
    try:
        with open(key_file, 'rb') as f:
            key = f.read()
    except FileNotFoundError:
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
    return key.decode() if isinstance(key, bytes) else key

def encrypt_value(value, key):
    """Encrypt a value using Fernet"""
    f = Fernet(key)
    return f.encrypt(value.encode()).decode()

def decrypt_value(encrypted_value, key):
    """Decrypt a value using Fernet"""
    f = Fernet(key)
    return f.decrypt(encrypted_value.encode()).decode()

def secure_settings(base_dir):
    """Set up secure settings with encryption"""
    # Create settings directory if it doesn't exist
    settings_dir = os.path.join(base_dir, '.settings')
    if not os.path.exists(settings_dir):
        os.makedirs(settings_dir)

    # Key files
    secret_key_file = os.path.join(settings_dir, '.django_secret')
    fernet_key_file = os.path.join(settings_dir, '.fernet_key')
    
    # Get or create Django secret key
    secret_key = get_or_create_secret_key(secret_key_file)
    
    # Get or create Fernet key for encryption
    fernet_key = get_or_create_fernet_key(fernet_key_file)
    
    return {
        'SECRET_KEY': secret_key,
        'FERNET_KEY': fernet_key,
    }