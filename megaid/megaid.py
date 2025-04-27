import time
import json
import jwt  # PyJWT library
import random
import base64

class MEGAID:
    """
    MEGAID: Immutable + Mutable Compound ID Generator (Snowflake + Dual JWT)

    Features:
    - Immutable Metadata (permanently locked at creation, signed by ADMIN key)
    - Mutable Metadata (updateable later, signed by SHARED key)
    - 64, 52 (JS Safe), or 32-bit Snowflake IDs
    - Dual key generation: ADMIN + SHARED
    - Customizable Default Metadata
    """

    def __init__(self, keys: dict, bit_size: int = 64, default_metadata: dict = None):
        if not all(k in keys for k in ("ADMIN", "SHARED")):
            raise ValueError("Keys must include both 'ADMIN' and 'SHARED'")
        if bit_size not in [64, 52, 32]:
            raise ValueError("bit_size must be one of: 64, 52, 32")

        self.admin_key = keys["ADMIN"]
        self.shared_key = keys["SHARED"]
        self.bit_size = 64  # Default always set to 64-bit unless explicitly overridden
        if bit_size != 64:
            self.bit_size = bit_size
        self.default_metadata = default_metadata or {
            "created_by": "MEGAID",
            "version": "2.0"
        }

    @staticmethod
    def generate_encryption_keys(admin_key: str = None) -> dict:
        def secure_random_key():
            return base64.urlsafe_b64encode(random.randbytes(32)).decode('utf-8')

        if admin_key:
            admin_secret = base64.urlsafe_b64encode(admin_key.encode('utf-8')).decode('utf-8')
            shared_secret = base64.urlsafe_b64encode((admin_key + "-shared").encode('utf-8')).decode('utf-8')
        else:
            admin_secret = secure_random_key()
            shared_secret = secure_random_key()

        return {
            "ADMIN": admin_secret,
            "SHARED": shared_secret
        }

    def create(self, immutable_data: dict = None, mutable_data: dict = None) -> str:
        megaid = self._create_megaid()
        timestamp, random_bits = self._decode_megaid(megaid)

        idata_payload = {
            "megaid": megaid,
            "date_created": timestamp,
            "random_bits": random_bits,
            "immutable_data": immutable_data or self.default_metadata
        }
        immutable_jwt = jwt.encode(idata_payload, self.admin_key, algorithm="HS256")

        mutable_payload = {
            "date_updated": timestamp,
            "mutable_data": (mutable_data or {})
        }
        mutable_jwt = jwt.encode(mutable_payload, self.shared_key, algorithm="HS256")

        return f"{megaid}:{immutable_jwt}:{mutable_jwt}"

    def read(self, compound_id: str) -> dict:
        try:
            parts = compound_id.split(":")
            if len(parts) != 3:
                raise ValueError("Invalid MEGAID format")

            megaid = int(parts[0])
            immutable_token = parts[1]
            mutable_token = parts[2]

            immutable_payload = jwt.decode(immutable_token, self.admin_key, algorithms=["HS256"])
            mutable_payload = jwt.decode(mutable_token, self.shared_key, algorithms=["HS256"])

            return {
                "megaid": immutable_payload["megaid"],
                "date_created": immutable_payload["date_created"],
                "date_updated": mutable_payload["date_updated"],
                "random_bits": immutable_payload["random_bits"],
                "immutable_data": immutable_payload["immutable_data"],
                "mutable_data": mutable_payload["mutable_data"]
            }
        except Exception as e:
            print(f"Error reading compound ID: {e}")
            return {}

    def update(self, compound_id: str, updates: dict) -> str:
        try:
            parts = compound_id.split(":")
            if len(parts) != 3:
                raise ValueError("Invalid MEGAID format")

            megaid = parts[0]
            immutable_token = parts[1]
            mutable_token = parts[2]

            mutable_payload = jwt.decode(mutable_token, self.shared_key, algorithms=["HS256"])
            current_data = mutable_payload.get("mutable_data", {})
            current_data.update(updates)

            new_payload = {
                "date_updated": int(time.time() * 1000),
                "mutable_data": current_data
            }
            new_mutable_jwt = jwt.encode(new_payload, self.shared_key, algorithm="HS256")

            return f"{megaid}:{immutable_token}:{new_mutable_jwt}"

        except Exception as e:
            print(f"Error updating compound ID: {e}")
            return ""

    def _create_megaid(self) -> int:
        timestamp = int(time.time() * 1000)
        if self.bit_size == 64:
            random_bits = random.getrandbits(22)
            megaid = (timestamp << 22) | random_bits
        elif self.bit_size == 52:
            random_bits = random.getrandbits(10)
            megaid = (timestamp << 10) | random_bits
        elif self.bit_size == 32:
            random_bits = random.getrandbits(2)
            megaid = (timestamp << 2) | random_bits
        return megaid

    def _decode_megaid(self, megaid: int):
        if self.bit_size == 64:
            timestamp = megaid >> 22
            random_bits = megaid & ((1 << 22) - 1)
        elif self.bit_size == 52:
            timestamp = megaid >> 10
            random_bits = megaid & ((1 << 10) - 1)
        elif self.bit_size == 32:
            timestamp = megaid >> 2
            random_bits = megaid & ((1 << 2) - 1)
        return timestamp, random_bits
