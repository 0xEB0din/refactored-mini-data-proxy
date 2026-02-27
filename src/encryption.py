from typing import List, Tuple
from umbral import (
    SecretKey, PublicKey, Signer, Capsule,
    encrypt, decrypt_original, generate_kfrags,
    reencrypt, decrypt_reencrypted,
    VerifiedKeyFrag, KeyFrag, VerifiedCapsuleFrag
)
from .logger import get_logger

log = get_logger(__name__)


def encrypt_data(
    data: bytes, public_key: PublicKey
) -> Tuple[bytes, Capsule]:
    """
    Encrypts the given data using the provided public key.

    Args:
        data: Raw bytes to be encrypted.
        public_key: Public key used for encryption.

    Returns:
        Tuple of (ciphertext, capsule).
    """
    capsule, ciphertext = encrypt(public_key, data)
    log.debug("Encrypted %d bytes of data", len(data))
    return ciphertext, capsule


def create_kfrags(
    delegating_sk: SecretKey,
    receiving_pk: PublicKey,
    signer: Signer,
    threshold: int,
    shares: int
) -> List[VerifiedKeyFrag]:
    """
    Generates key fragments (kfrags) for proxy re-encryption.

    Args:
        delegating_sk: Secret key of the delegator (Alice).
        receiving_pk: Public key of the receiver (Bob).
        signer: Signer for the delegating party.
        threshold: Min kfrags required for decryption.
        shares: Total kfrags to generate.

    Returns:
        List of generated verified key fragments.
    """
    signer = Signer(delegating_sk)
    kfrags = generate_kfrags(
        delegating_sk=delegating_sk,
        receiving_pk=receiving_pk,
        signer=signer,
        threshold=threshold,
        shares=shares,
        sign_delegating_key=True,
        sign_receiving_key=True
    )
    log.debug(
        "Generated %d kfrags (threshold=%d)", shares, threshold
    )
    return kfrags


def reencrypt_data(
    capsule: Capsule,
    verified_kfrag: VerifiedKeyFrag
) -> VerifiedCapsuleFrag:
    """
    Re-encrypts a capsule using a verified key fragment.

    Args:
        capsule: The capsule tied to the ciphertext.
        verified_kfrag: Verified key fragment for
            re-encryption.

    Returns:
        A verified capsule fragment.
    """
    cfrag = reencrypt(capsule, verified_kfrag)
    return cfrag


def decrypt_data(
    secret_key: SecretKey,
    capsule: Capsule,
    ciphertext: bytes
) -> bytes:
    """
    Decrypts data encrypted with the owner's public key.

    Args:
        secret_key: Owner's secret key.
        capsule: Capsule associated with the ciphertext.
        ciphertext: The encrypted data.

    Returns:
        Decrypted plaintext bytes.
    """
    decrypted_data = decrypt_original(
        secret_key, capsule, ciphertext
    )
    return decrypted_data


def decrypt_reencrypted_data(
    receiving_sk: SecretKey,
    delegating_pk: PublicKey,
    capsule: Capsule,
    verified_cfrags: List[VerifiedCapsuleFrag],
    ciphertext: bytes
) -> bytes:
    """
    Decrypts re-encrypted data using the receiver's key.

    Args:
        receiving_sk: Receiver's secret key.
        delegating_pk: Delegator's public key.
        capsule: Capsule used for decryption.
        verified_cfrags: Verified re-encrypted capsule
            fragments.
        ciphertext: Ciphertext to be decrypted.

    Returns:
        Decrypted plaintext bytes.
    """
    decrypted_data = decrypt_reencrypted(
        receiving_sk=receiving_sk,
        delegating_pk=delegating_pk,
        capsule=capsule,
        verified_cfrags=verified_cfrags,
        ciphertext=ciphertext
    )
    return decrypted_data


def deserialize_kfrag(hex_kfrag: str) -> KeyFrag:
    """
    Deserializes a hex string back into a KeyFrag.

    Args:
        hex_kfrag: Hex-encoded key fragment.

    Returns:
        Deserialized KeyFrag object.
    """
    return KeyFrag.from_bytes(bytes.fromhex(hex_kfrag))
