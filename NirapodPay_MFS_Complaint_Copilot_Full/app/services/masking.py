def mask_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        return "Unknown"
    return " ".join(part[0] + "*" * max(len(part) - 1, 1) for part in cleaned.split())


def mask_phone(phone: str) -> str:
    digits = "".join(character for character in phone if character.isdigit())
    if len(digits) < 4:
        return "****"
    return "*" * max(len(digits) - 4, 4) + digits[-4:]
