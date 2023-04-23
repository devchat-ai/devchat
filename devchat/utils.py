import re


def is_valid_hash(hash_str):
    """Check if a string is a valid hash value."""
    # Hash values are usually alphanumeric with a fixed length
    # depending on the algorithm used to generate them
    pattern = re.compile(r'^[a-fA-F0-9]{40}$')  # Example pattern for SHA-1 hash
    return bool(pattern.match(hash_str))
