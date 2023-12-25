def mask_sensitive_data(data):
    return "*" * (len(data) - 4) + data[-4:]
