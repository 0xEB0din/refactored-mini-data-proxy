from typing import List, Tuple
from umbral import (
    SecretKey, PublicKey, Signer, Capsule,
    encrypt, decrypt_original, generate_kfrags, reencrypt, decrypt_reencrypted,
    VerifiedKeyFrag, KeyFrag, VerifiedCapsuleFrag
)


def encrypt_data(data: bytes, public_key: PublicKey) -> Tuple[bytes, Capsule]:
    """
    Encrypts the given data using the provided public key.

    Args:
        data (bytes): Data to be encrypted.
        public_key (PublicKey): Public key used for encryption.

    Returns:
        Tuple[bytes, Capsule]: A tuple containing the ciphertext and the capsule.
    """
    capsule, ciphertext = encrypt(public_key, data)
    return ciphertext, capsule


def create_kfrags(
    delegating_sk: SecretKey,
    receiving_pk: PublicKey,
    signer: Signer,
    threshold: int,
    shares: int
) -> list[VerifiedKeyFrag]:
    """
    Generates key fragments (kfrags) for proxy re-encryption.

    Args:
        delegating_sk (SecretKey): Secret key of the delegating party.
        receiving_pk (PublicKey): Public key of the receiving party.
        signer (Signer): Signer for the delegating party.
        threshold (int): Minimum number of kfrags required for decryption.
        shares (int): Total number of kfrags to generate.

    Returns:
        List[KeyFrag]: List of generated key fragments (kfrags).
    """
    signer = Signer(delegating_sk)  # Ensure the signer is correctly initialized
    kfrags = generate_kfrags(
        delegating_sk=delegating_sk,
        receiving_pk=receiving_pk,
        signer=signer,
        threshold=threshold,
        shares=shares,
        sign_delegating_key=True,
        sign_receiving_key=True
    )
    return kfrags


def reencrypt_data(capsule: Capsule, verified_kfrag: VerifiedKeyFrag) -> VerifiedCapsuleFrag:
    """
    Reencrypts a capsule using a verified key fragment.

    Args:
        capsule (umbral.Capsule): The capsule associated with the ciphertext.
        verified_kfrag (umbral.VerifiedKeyFrag): The verified key fragment used for reencryption.

    Returns:
        umbral.VerifiedCapsuleFrag: A fragment of the reencrypted capsule.
    """
    cfrag = reencrypt(capsule, verified_kfrag)
    return cfrag


def decrypt_data(secret_key: SecretKey, capsule: Capsule, ciphertext: bytes) -> bytes:
    """
    Decrypts data that was encrypted directly with the recipient's public key.

    Args:
        secret_key (SecretKey): The secret key of the receiver to decrypt the data.
        capsule (Capsule): The capsule associated with the ciphertext.
        ciphertext (bytes): The encrypted data.

    Returns:
        bytes: The decrypted data.
    """
    decrypted_data = decrypt_original(secret_key, capsule, ciphertext)
    return decrypted_data


def decrypt_reencrypted_data(
    receiving_sk: SecretKey,
    delegating_pk: PublicKey,
    capsule: Capsule,
    verified_cfrags: List[VerifiedCapsuleFrag],
    ciphertext: bytes
) -> bytes:
    """
    Decrypts the re-encrypted data using the receiving party's secret key.

    Args:
        receiving_sk (SecretKey): Secret key of the receiving party.
        delegating_pk (PublicKey): Public key of the delegating party.
        capsule (Capsule): Capsule used for decryption.
        verified_cfrags (List[VerifiedCapsuleFrag]): List of verified re-encrypted capsule fragments.
        ciphertext (bytes): Ciphertext to be decrypted.

    Returns:
        bytes: Decrypted data.
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
    Deserializes a hexadecimal string back into a Kfrag object.

    Args:
        hex_kfrag (str): The hexadecimal string representing a Kfrag.

    Returns:
        KeyFrag: The deserialized Kfrag object.
    """
    return KeyFrag.from_bytes(bytes.fromhex(hex_kfrag))