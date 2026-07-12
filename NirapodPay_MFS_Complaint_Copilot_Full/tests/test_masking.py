from app.services.masking import mask_name, mask_phone


def test_mask_phone_reveals_only_last_four_digits():
    assert mask_phone("+8801712345678").endswith("5678")
    assert "1234" not in mask_phone("+8801712345678")


def test_mask_name_hides_most_characters():
    masked = mask_name("Amina Rahman")
    assert masked.startswith("A")
    assert "mina" not in masked
