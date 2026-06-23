"""AWS KMS envelope encryption.

The KMS master key never leaves KMS: we only ever call GenerateDataKey (encrypt
path) and Decrypt (decrypt path). The data key is used locally with AES-256-GCM
to wrap the payload, and only ciphertext is stored. This is also why we don't
hand the secret key to KMS directly — an ML-DSA-65 SK is ~4 KB, at KMS's limit.
"""

import os

import boto3
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from config import settings

_kms = boto3.client("kms", region_name=settings.aws_region)

_NONCE_BYTES = 12


def _wipe(buf: bytearray) -> None:
    buf[:] = b"\x00" * len(buf)


def envelope_encrypt(plaintext: bytes) -> tuple[bytes, bytes, bytes]:
    """Seal `plaintext`. Returns (ciphertext, encrypted_data_key, nonce).

    `ciphertext` includes the GCM tag. `encrypted_data_key` is the KMS
    CiphertextBlob of the AES data key. The plaintext data key is zeroed before
    returning and never persisted.
    """
    resp = _kms.generate_data_key(KeyId=settings.kms_key_id, KeySpec="AES_256")
    data_key = bytearray(resp["Plaintext"])
    try:
        nonce = os.urandom(_NONCE_BYTES)
        ciphertext = AESGCM(bytes(data_key)).encrypt(nonce, plaintext, None)
    finally:
        _wipe(data_key)
    return ciphertext, resp["CiphertextBlob"], nonce


def envelope_decrypt(
    ciphertext: bytes, encrypted_data_key: bytes, nonce: bytes
) -> bytes:
    """Reverse of `envelope_encrypt`. KMS decrypts the data key, which we use
    locally to decrypt the payload. The plaintext data key is zeroed before
    returning. The caller owns the returned plaintext and must zero it."""
    resp = _kms.decrypt(CiphertextBlob=encrypted_data_key)
    data_key = bytearray(resp["Plaintext"])
    try:
        return AESGCM(bytes(data_key)).decrypt(nonce, ciphertext, None)
    finally:
        _wipe(data_key)
