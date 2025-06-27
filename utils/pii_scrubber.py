import re

def scrub_pii(text: str) -> str:
    # Example: Replace date formats DD-MM-YYYY or DD/MM/YYYY
    text = re.sub(r'\b\d{2}[/-]\d{2}[/-]\d{4}\b', '[DATE]', text)
    
    # Example: Replace 10-digit phone numbers
    text = re.sub(r'\b\d{10}\b', '[PHONE]', text)
    
    # Example: Replace email addresses
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]', text)
    
    return text
