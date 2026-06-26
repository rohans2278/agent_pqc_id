"""ML-DSA-65 sign/verify and the property tamper relies on."""

import crypto

MSG = b"canonical payload bytes"


def test_sign_verify_roundtrip():
    public_key, secret_key = crypto.keygen()
    assert crypto.verify(public_key, MSG, crypto.sign(secret_key, MSG))


def test_verify_rejects_wrong_message():
    public_key, secret_key = crypto.keygen()
    signature = crypto.sign(secret_key, MSG)
    assert not crypto.verify(public_key, b"different", signature)


def test_signature_from_unrelated_key_fails():
    # This is exactly what tamper does: a signature from a fresh, unrelated
    # secret key must not verify against the registered public key.
    public_key, _ = crypto.keygen()
    _, rogue_secret_key = crypto.keygen()
    assert not crypto.verify(public_key, MSG, crypto.sign(rogue_secret_key, MSG))
