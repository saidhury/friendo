import re
from typing import Tuple, Dict

class PIIMaskingService:
    """Service for masking Personally Identifiable Information before LLM calls."""
    
    # Patterns for PII detection
    PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b',
        'ssn': r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
        'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    }
    
    # Common name patterns (simplified)
    NAME_PREFIXES = ['mr', 'mrs', 'ms', 'dr', 'prof']
    
    # Location indicators
    LOCATION_INDICATORS = [
        'street', 'st', 'avenue', 'ave', 'road', 'rd', 'drive', 'dr',
        'lane', 'ln', 'boulevard', 'blvd', 'city', 'state', 'zip',
        'apartment', 'apt', 'suite', 'ste', 'floor', 'building'
    ]
    
    def __init__(self):
        self._mask_map: Dict[str, str] = {}
        self._reverse_map: Dict[str, str] = {}
        self._counter = 0
    
    def _generate_placeholder(self, pii_type: str) -> str:
        """Generate a unique placeholder for masked PII."""
        self._counter += 1
        return f"[{pii_type.upper()}_{self._counter}]"
    
    def mask_text(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Mask all PII in text and return masked text with mapping.
        
        Returns:
            Tuple of (masked_text, mapping_dict)
        """
        self._mask_map = {}
        self._reverse_map = {}
        self._counter = 0
        masked_text = text
        
        # Mask emails
        for match in re.finditer(self.PATTERNS['email'], masked_text, re.IGNORECASE):
            original = match.group()
            placeholder = self._generate_placeholder('EMAIL')
            self._mask_map[placeholder] = original
            self._reverse_map[original] = placeholder
            masked_text = masked_text.replace(original, placeholder, 1)
        
        # Mask phone numbers
        for match in re.finditer(self.PATTERNS['phone'], masked_text):
            original = match.group()
            if original not in self._reverse_map:
                placeholder = self._generate_placeholder('PHONE')
                self._mask_map[placeholder] = original
                self._reverse_map[original] = placeholder
                masked_text = masked_text.replace(original, placeholder, 1)
        
        # Mask SSNs
        for match in re.finditer(self.PATTERNS['ssn'], masked_text):
            original = match.group()
            if original not in self._reverse_map:
                placeholder = self._generate_placeholder('SSN')
                self._mask_map[placeholder] = original
                self._reverse_map[original] = placeholder
                masked_text = masked_text.replace(original, placeholder, 1)
        
        # Mask credit cards
        for match in re.finditer(self.PATTERNS['credit_card'], masked_text):
            original = match.group()
            if original not in self._reverse_map:
                placeholder = self._generate_placeholder('CARD')
                self._mask_map[placeholder] = original
                self._reverse_map[original] = placeholder
                masked_text = masked_text.replace(original, placeholder, 1)
        
        # Mask potential names (words after name prefixes)
        for prefix in self.NAME_PREFIXES:
            pattern = rf'\b{prefix}\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
            for match in re.finditer(pattern, masked_text, re.IGNORECASE):
                original = match.group(1)
                if original not in self._reverse_map:
                    placeholder = self._generate_placeholder('NAME')
                    self._mask_map[placeholder] = original
                    self._reverse_map[original] = placeholder
                    masked_text = masked_text.replace(original, placeholder, 1)
        
        # Mask locations (addresses)
        for indicator in self.LOCATION_INDICATORS:
            pattern = rf'\b(\d+\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+{indicator})\b'
            for match in re.finditer(pattern, masked_text, re.IGNORECASE):
                original = match.group()
                if original not in self._reverse_map:
                    placeholder = self._generate_placeholder('LOCATION')
                    self._mask_map[placeholder] = original
                    self._reverse_map[original] = placeholder
                    masked_text = masked_text.replace(original, placeholder, 1)
        
        return masked_text, self._mask_map.copy()
    
    def unmask_text(self, masked_text: str, mask_map: Dict[str, str]) -> str:
        """
        Restore original PII values in text using the mapping.
        """
        unmasked_text = masked_text
        for placeholder, original in mask_map.items():
            unmasked_text = unmasked_text.replace(placeholder, original)
        return unmasked_text
    
    def is_safe_for_llm(self, text: str) -> bool:
        """
        Check if text is safe to send to LLM (no obvious PII).
        """
        for pattern in self.PATTERNS.values():
            if re.search(pattern, text, re.IGNORECASE):
                return False
        return True


# Singleton instance
_pii_service = None

def get_pii_masking_service() -> PIIMaskingService:
    """Get or create the PII masking service singleton."""
    global _pii_service
    if _pii_service is None:
        _pii_service = PIIMaskingService()
    return _pii_service
