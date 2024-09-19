import re

def validate_password(password):
    if len(password) < 8 or not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True
