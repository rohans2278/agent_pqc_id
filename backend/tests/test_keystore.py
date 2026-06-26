"""Key lifecycle: create → load → sign/verify, and tamper detection.
Touches Postgres + KMS + liboqs."""

import crypto
import keystore

MSG = b"payload"


def test_create_then_load_roundtrips(db):
    agent = keystore.create_keypair_for_agent(db, "ks-roundtrip")
    secret_key = keystore.load_secret_key(agent)
    assert crypto.verify(agent.public_key, MSG, crypto.sign(secret_key, MSG))


def test_tamper_keeps_identity_but_breaks_signature(db):
    agent = keystore.create_keypair_for_agent(db, "ks-tamper")
    registered_public_key = bytes(agent.public_key)

    keystore.tamper_agent(db, agent.id)

    # The registered public key (the identity) is unchanged...
    assert agent.public_key == registered_public_key
    # ...but the now-rogue secret key no longer signs for it.
    secret_key = keystore.load_secret_key(agent)
    assert not crypto.verify(agent.public_key, MSG, crypto.sign(secret_key, MSG))
