"""KMS envelope encryption round-trip. Hits real AWS KMS."""

import kms


def test_envelope_roundtrip():
    secret = b"an ML-DSA secret key stand-in"
    ciphertext, encrypted_data_key, nonce = kms.envelope_encrypt(secret)

    assert ciphertext != secret
    assert kms.envelope_decrypt(ciphertext, encrypted_data_key, nonce) == secret


def test_each_encrypt_uses_a_fresh_nonce():
    c1, _, n1 = kms.envelope_encrypt(b"same")
    c2, _, n2 = kms.envelope_encrypt(b"same")
    assert n1 != n2
    assert c1 != c2
