# MEGAID

Ultra-light Snowflake + JWT Compound ID Generator. Secure. Tamper-proof. JavaScript-safe.

---

## Objective

**MEGAID** was created for developers, engineers, and architects who need a fast, secure, and flexible way to generate globally unique, tamper-resistant identifiers across distributed systems.

At its core, MEGAID fuses two trusted technologies — Snowflake IDs and JWT-secured metadata — to produce lightweight, verifiable compound IDs. Whether you're building microservices, APIs, distributed databases, or mobile apps, MEGAID ensures every object, user, or event has a unique, cryptographically verifiable fingerprint.

MEGAID is designed for whenever reliability, scalability, and cross-platform compatibility matter. It works seamlessly across Python, JavaScript (52-bit safe), 32-bit embedded systems, and modern 64-bit cloud infrastructure.

Traditional ID solutions (like UUIDs or database auto-increments) often fall short at scale — bulky formats, collision risks, lack of verifiability. MEGAID solves these problems by embedding immutable and mutable metadata directly into dual-signed JWTs, providing not just IDs — but a verifiable history of creation and evolution.

Simple. Powerful. Open. Secure.  
That’s the MEGAID way.

---

## About the Twitter Snowflake Algorithm

**Who**:  
Developed by Twitter's engineering team in 2010 to solve distributed ID generation challenges.

**What**:  
Snowflake is a 64-bit distributed unique ID generator. Each ID encodes a timestamp, machine ID, and sequence number, ensuring uniqueness without centralized coordination.

**When**:  
Built during Twitter’s global expansion when UUIDs and database IDs became bottlenecks. Open-sourced internally shortly after.

**Why**:  
Traditional ID systems cause race conditions, collisions, and scalability limits. Snowflake solves this by making ID generation local, fast, and time-sortable.

**How**:  
Each Snowflake ID typically consists of:
- 42 bits for timestamp (in milliseconds)
- 10 bits for machine/worker ID
- 12 bits for sequence number (incremented per millisecond)

This guarantees:
- Global uniqueness
- Rough chronological sorting
- Massive throughput (millions of IDs/sec)

**MEGAID** extends Snowflake by securely attaching cryptographically signed immutable and mutable metadata to every ID — preserving all Snowflake strengths while enhancing flexibility and security.

---

## Install

From GitHub:
```bash
pip install git+https://github.com/MEGALab/MEGAID-python.git
```

From local clone:
```bash
pip install .
```

---

## Quick Start

```python
from megaid import MEGAID

# Step 1: Generate secure ADMIN and SHARED keys
keys = MEGAID.generate_encryption_keys()

# Step 2: Initialize MEGAID for JavaScript-safe (52-bit) IDs
megaid = MEGAID(keys, bit_size=52)

# Step 3: Create a new MEGAID
immutable_data = {"username": "startrekfan", "account_type": "officer"}
mutable_data = {"status": "pending"}

new_id = megaid.create(immutable_data, mutable_data)

# Step 4: Read the MEGAID
print(megaid.read(new_id))

# Step 5: Update the MEGAID (mutable fields only)
updated_id = megaid.update(new_id, {"status": "approved", "rank": "Captain"})
print(megaid.read(updated_id))
```

---

## Key Generation Examples

### Without Admin Key

```python
from megaid import MEGAID

# Generate random ADMIN and SHARED keys
keys = MEGAID.generate_encryption_keys()
```

### With Admin Key and Default Metadata

```python
from megaid import MEGAID

# Generate keys using an ADMIN master key and define default metadata
admin_key = "MASTER_SECRET"
default_metadata = {"created_by": "MegaLab", "version": "2.0", "environment": "production"}

keys = MEGAID.generate_encryption_keys(admin_key)
megaid = MEGAID(keys, bit_size=64, default_metadata=default_metadata)

# Now any MEGAID created without explicitly passed immutable_data will use default_metadata.
```

---

## Payload Example

```json
{
  "megaid": 1452668717294426112,
  "date_created": 1714233895123,
  "date_updated": 1714234000000,
  "random_bits": 1234567,
  "immutable_data": {
    "username": "startrekfan",
    "account_type": "officer"
  },
  "mutable_data": {
    "status": "approved",
    "rank": "Captain"
  }
}
```

---

## Features

- 64-bit full Snowflake IDs
- 52-bit JavaScript-safe Snowflake IDs (fits inside `Number.MAX_SAFE_INTEGER`)
- 32-bit minimal IDs for embedded systems
- Cryptographically signed Immutable and Mutable metadata
- Dual key system (ADMIN key for immutable, SHARED key for mutable)
- Default metadata customization
- Fast, secure, tamper-resistant ID generation
- Simple create, update, read APIs

---

## License

This project is licensed under the **GNU Affero General Public License v3.0**.

See [LICENSE](LICENSE) for full details.

---
