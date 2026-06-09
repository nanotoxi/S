import re

def validate_linkedin(url: str) -> bool:
    pattern = r'^https?:\/\/(www\.)?linkedin\.com\/in\/[a-zA-Z0-9_-]+\/?$'
    return bool(re.match(pattern, url))

def validate_github(url: str) -> bool:
    pattern = r'^https?:\/\/(www\.)?github\.com\/[a-zA-Z0-9_-]+\/?$'
    return bool(re.match(pattern, url))

def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
