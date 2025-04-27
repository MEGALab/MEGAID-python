import pytest
from megaid import MEGAID

def test_basic_create_read_update():
    secret = MEGAID.generate_encryption_key()
    gen = MEGAID(secret_key=secret, bit_size=52)

    compound_id = gen.create({"testkey": "testvalue"})
    assert compound_id

    payload = gen.read(compound_id)
    assert "snowflake" in payload
    assert "data" in payload
    assert payload["data"]["testkey"] == "testvalue"

    updated_id = gen.update(compound_id, {"newkey": "newvalue"})
    updated_payload = gen.read(updated_id)
    assert updated_payload["data"]["newkey"] == "newvalue"
