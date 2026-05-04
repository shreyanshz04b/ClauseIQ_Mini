UNSAFE_PATTERNS = {
    'ignore previous', 'ignore all', 'system prompt', 'jailbreak', 'bypass',
    'hack', 'malware', 'forget instructions', 'act as', 'pretend', 'dan mode', 
    'forget your', 'disregard', 'override instructions'
}

def classify(text):
    if not text:
        return 'SAFE'
    
    query_lower = text.lower().strip()
    
    for pattern in UNSAFE_PATTERNS:
        if pattern in query_lower:
            return 'UNSAFE'
    return 'SAFE'
