import hashlib
from pathlib import Path

# 0x12 (SHA2-256) + 0x20 (32-byte digest), hex-encoded
SHA2_256_MULTIHASH_PREFIX = "1220"


def sha256_multihash(path: Path) -> str:
    """
    SHA2-256 multihash for STAC file:checksum.
    https://github.com/stac-extensions/file
    """
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"{SHA2_256_MULTIHASH_PREFIX}{digest.hexdigest()}"
