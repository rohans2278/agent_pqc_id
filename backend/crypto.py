"""ML-DSA-65 (CRYSTALS-Dilithium, NIST Level 3) keygen / sign / verify.

Thin wrapper over liboqs (the `oqs` Python binding). Key sealing and zeroing of
plaintext secret keys live in keystore.py / signing.py, not here.
"""

import oqs

MECHANISM = "ML-DSA-65"

# Fail loudly on an old liboqs that only exposes the pre-standard name, rather
# than silently signing with the wrong algorithm.
if MECHANISM not in oqs.get_enabled_sig_mechanisms():
    raise RuntimeError(
        f"liboqs does not expose {MECHANISM!r}. This build is too old "
        f"(older liboqs calls it 'Dilithium3'). Rebuild with a current liboqs."
    )


def keygen() -> tuple[bytes, bytes]:
    """Return a fresh (public_key, secret_key) pair."""
    with oqs.Signature(MECHANISM) as signer:
        public_key = signer.generate_keypair()
        secret_key = signer.export_secret_key()
    return public_key, secret_key


def sign(secret_key: bytes | bytearray, message: bytes) -> bytes:
    """Sign `message` with `secret_key`. liboqs frees its own copy of the key on
    exit; the caller still owns and must zero the `secret_key` buffer it passed."""
    with oqs.Signature(MECHANISM, bytes(secret_key)) as signer:
        return signer.sign(message)


def verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    """True iff `signature` is valid for `message` under `public_key`."""
    with oqs.Signature(MECHANISM) as verifier:
        return verifier.verify(message, signature, public_key)
