import hashlib

def generate_file_hash(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read in blocks to handle memory efficiently
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# Replace with your actual filename
print(f"Your Master Hash is: {generate_file_hash('reservoir_keywords_db_v3.json')}")