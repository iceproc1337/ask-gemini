from uuid import UUID
import secrets


def secure_uuid4():
    return UUID(int=secrets.randbelow(1 << 128))
