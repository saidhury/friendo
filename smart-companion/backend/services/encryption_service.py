import base64
import json
from typing import Any
from cryptography.fernet import Fernet, InvalidToken
from config import get_settings

class EncryptionService:
    """Service for encrypting and decrypting sensitive data using Fernet (AES)."""
    
    def __init__(self):
        settings = get_settings()
        key = settings.ENCRYPTION_KEY
        
        # Ensure key is properly formatted for Fernet
        try:
            # Try to use the key directly
            self.fernet = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception:
            # Generate a proper key from the provided string
            key_bytes = key.encode()[:32].ljust(32, b'0')
            proper_key = base64.urlsafe_b64encode(key_bytes)
            self.fernet = Fernet(proper_key)
    
    def encrypt(self, data: Any) -> str:
        """
        Encrypt data and return base64-encoded string.
        Accepts strings, dicts, or lists.
        """
        if data is None:
            return ""
        
        # Convert to JSON string if not already a string
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data)
        else:
            data_str = str(data)
        
        # Encrypt and return as string
        encrypted = self.fernet.encrypt(data_str.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_data: str) -> Any:
        """
        Decrypt data and return original value.
        Attempts to parse as JSON, returns string if not valid JSON.
        """
        if not encrypted_data:
            return None
        
        try:
            decrypted = self.fernet.decrypt(encrypted_data.encode())
            decrypted_str = decrypted.decode()
            
            # Try to parse as JSON
            try:
                return json.loads(decrypted_str)
            except json.JSONDecodeError:
                return decrypted_str
                
        except InvalidToken:
            # Return empty if decryption fails (corrupted or wrong key)
            return None
    
    def encrypt_json(self, data: dict | list) -> str:
        """Encrypt a JSON-serializable object."""
        return self.encrypt(data)
    
    def decrypt_json(self, encrypted_data: str, default: Any = None) -> Any:
        """Decrypt to a JSON object with a default fallback."""
        result = self.decrypt(encrypted_data)
        return result if result is not None else default


# Singleton instance
_encryption_service = None

def get_encryption_service() -> EncryptionService:
    """Get or create the encryption service singleton."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service
