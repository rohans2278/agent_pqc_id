"""Agent key lifecycle: issue a keypair, load the secret key, and tamper.

This is the only place an agent's secret key is created or unsealed. Plaintext
secret keys are handled in `bytearray`s and zeroed as soon as we're done with
them. The registered public key is the agent's identity and is set once, at
creation — tampering never touches it, which is exactly what makes tamper
detectable.
"""

import uuid

import crypto
import kms
from models import Agent
from sqlalchemy.orm import Session


def wipe(buf: bytearray) -> None:
    """Zero a mutable secret buffer in place."""
    buf[:] = b"\x00" * len(buf)


def create_keypair_for_agent(db: Session, name: str) -> Agent:
    """Generate an ML-DSA-65 keypair, store the public key as the agent's
    identity and the secret key sealed via KMS envelope encryption."""
    public_key, secret_key = crypto.keygen()
    sk = bytearray(secret_key)
    try:
        ciphertext, encrypted_data_key, nonce = kms.envelope_encrypt(bytes(sk))
    finally:
        wipe(sk)

    agent = Agent(
        name=name,
        public_key=public_key,
        encrypted_secret_key=ciphertext,
        encrypted_data_key=encrypted_data_key,
        nonce=nonce,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def load_secret_key(agent: Agent) -> bytearray:
    """Unseal the agent's secret key for signing. Returns a `bytearray` the
    caller MUST zero (via `_wipe`) immediately after use."""
    plaintext = kms.envelope_decrypt(
        agent.encrypted_secret_key, agent.encrypted_data_key, agent.nonce
    )
    return bytearray(plaintext)


def tamper_agent(db: Session, agent_id: uuid.UUID) -> Agent | None:
    """Simulate a compromise: replace the agent's stored secret key with a
    random one (a fresh, unrelated keypair's SK), leaving the registered public
    key untouched. Signatures will no longer verify against it."""
    agent = db.get(Agent, agent_id)
    if agent is None:
        return None

    _, rogue_secret_key = crypto.keygen()  # the rogue public key is discarded
    sk = bytearray(rogue_secret_key)
    try:
        ciphertext, encrypted_data_key, nonce = kms.envelope_encrypt(bytes(sk))
    finally:
        wipe(sk)

    agent.encrypted_secret_key = ciphertext
    agent.encrypted_data_key = encrypted_data_key
    agent.nonce = nonce
    db.commit()
    db.refresh(agent)
    return agent
