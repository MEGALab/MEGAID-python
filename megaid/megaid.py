#!/usr/bin/env python3
import time
import json
import jwt  # PyJWT library
import random
import base64
import os
from pathlib import Path
from dotenv import load_dotenv

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

    def __init__(
        self, 
        keys: dict = None, 
        bit_size: int = 64, 
        default_metadata: dict = None
    ):
        """Initialize MEGAID with keys from dict or environment."""
        # If no keys provided, try to load from environment
        keys = keys or self.load_or_generate_keys()

        if not all(k in keys for k in ("ADMIN", "SHARED")):
            raise ValueError("Keys must include both 'ADMIN' and 'SHARED'")
        if bit_size not in [64, 52, 32]:
            raise ValueError("bit_size must be one of: 64, 52, 32")

        self.admin_key = keys["ADMIN"]
        self.shared_key = keys["SHARED"]
        self.bit_size = bit_size
        self.default_metadata = default_metadata or {
            "created_by": "MEGAID",
            "version": "2.0"
        }

    @classmethod
    def load_or_generate_keys(cls, env_file: str = None) -> dict:
        """Load keys from environment or generate new ones and save them."""
        # Try to load .env file if specified
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to find .env in various locations
            search_paths = [
                Path(".env"),  # Current directory
                Path("../.env"),  # Parent directory
                Path(__file__).parent.parent / ".env",  # Package root
            ]
            for env_path in search_paths:
                if env_path.exists():
                    load_dotenv(env_path)
                    break

        # Check for environment variables
        admin_key = os.getenv("MEGAID_ADMIN_KEY")
        shared_key = os.getenv("MEGAID_SHARED_KEY")

        if admin_key and shared_key:
            return {"ADMIN": admin_key, "SHARED": shared_key}

        # Generate new keys
        keys = cls.generate_encryption_keys()

        # Save to .env file
        env_content = [
            f"MEGAID_ADMIN_KEY='{keys['ADMIN']}'",
            f"MEGAID_SHARED_KEY='{keys['SHARED']}'"
        ]
        
        with open(".env", "w") as f:
            f.write("\n".join(env_content))
        
        # Also set them in current environment
        os.environ["MEGAID_ADMIN_KEY"] = keys["ADMIN"]
        os.environ["MEGAID_SHARED_KEY"] = keys["SHARED"]
        
        return keys

    @staticmethod
    def generate_encryption_keys(admin_key: str = None) -> dict:
        """Generate new encryption keys."""
        def secure_random_key():
            return base64.urlsafe_b64encode(
                random.randbytes(32)
            ).decode('utf-8')

        if admin_key:
            admin_secret = base64.urlsafe_b64encode(
                admin_key.encode('utf-8')
            ).decode('utf-8')
            shared_secret = base64.urlsafe_b64encode(
                (admin_key + "-shared").encode('utf-8')
            ).decode('utf-8')
        else:
            admin_secret = secure_random_key()
            shared_secret = secure_random_key()

        return {
            "ADMIN": admin_secret,
            "SHARED": shared_secret
        }

    def create(self, immutable_data: dict = None, mutable_data: dict = None) -> str:
        """Create a new compound ID with optional metadata."""
        megaid = self._create_megaid()
        timestamp, random_bits = self._decode_megaid(megaid)

        idata_payload = {
            "megaid": megaid,
            "date_created": timestamp,
            "random_bits": random_bits,
            "immutable_data": immutable_data or self.default_metadata
        }
        immutable_jwt = jwt.encode(
            idata_payload,
            self.admin_key,
            algorithm="HS256"
        )

        mutable_payload = {
            "date_updated": timestamp,
            "mutable_data": (mutable_data or {})
        }
        mutable_jwt = jwt.encode(
            mutable_payload,
            self.shared_key,
            algorithm="HS256"
        )

        return f"{megaid}:{immutable_jwt}:{mutable_jwt}"

    def read(self, compound_id: str) -> dict:
        """Read data from a compound ID."""
        try:
            parts = compound_id.split(":")
            if len(parts) != 3:
                raise ValueError("Invalid MEGAID format")

            # Parse tokens
            _, immutable_token, mutable_token = parts

            # Decode tokens
            immutable_payload = jwt.decode(
                immutable_token, 
                self.admin_key, 
                algorithms=["HS256"]
            )
            mutable_payload = jwt.decode(
                mutable_token, 
                self.shared_key, 
                algorithms=["HS256"]
            )

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
        """Update mutable data in a compound ID."""
        try:
            parts = compound_id.split(":")
            if len(parts) != 3:
                raise ValueError("Invalid MEGAID format")

            megaid = parts[0]
            immutable_token = parts[1]
            mutable_token = parts[2]

            # Decode mutable token
            mutable_payload = jwt.decode(
                mutable_token, 
                self.shared_key, 
                algorithms=["HS256"]
            )
            current_data = mutable_payload.get("mutable_data", {})
            current_data.update(updates)

            # Create new payload
            new_payload = {
                "date_updated": int(time.time() * 1000),
                "mutable_data": current_data
            }
            
            # Encode new token
            new_mutable_jwt = jwt.encode(
                new_payload, 
                self.shared_key, 
                algorithm="HS256"
            )

            return f"{megaid}:{immutable_token}:{new_mutable_jwt}"

        except Exception as e:
            print(f"Error updating compound ID: {e}")
            return ""

    def _create_megaid(self) -> int:
        """Create a new snowflake ID."""
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
        """Decode timestamp and random bits from a snowflake ID."""
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