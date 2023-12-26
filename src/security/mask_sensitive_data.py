def mask_sensitive_data(data):
    if len(data) >= 4:
        return "*" * (len(data) - 4) + data[-4:]
    else:
        return data
