from typing import Dict, Any, Tuple
from umbral import (
    SecretKey, PublicKey, Signer, Capsule,
    VerifiedKeyFrag,
)
from .encryption import (
    encrypt_data, create_kfrags, reencrypt_data,
    decrypt_reencrypted_data,
)
from .did_document import create_did_document
from .logger import get_logger

log = get_logger(__name__)


class DataStorageError(Exception):
    """Raised when data storage or retrieval fails."""


class DecryptionError(Exception):
    """Raised when the decryption process fails."""


def store_data(
    database: Dict[str, Any],
    asset_id: str,
    data: bytes,
    access_url: str,
    owner_key: SecretKey,
    owner_signer: Signer,
    consumer_key: PublicKey,
) -> None:
    """
    Encrypts and stores data with its DID document.

    Args:
        database: In-memory store.
        asset_id: Unique data-asset identifier.
        data: Raw bytes to encrypt and store.
        access_url: URL recorded in the DID document.
        owner_key: Data owner's secret key.
        owner_signer: Signer for the owner.
        consumer_key: Consumer's public key.

    Raises:
        DataStorageError: On storage failure.
    """
    if not all([
        asset_id, data, access_url,
        owner_key, owner_signer, consumer_key,
    ]):
        raise ValueError("All parameters are required")

    try:
        owner_pk = owner_key.public_key()
        ciphertext, capsule = encrypt_data(data, owner_pk)
        kfrags = create_kfrags(
            owner_key, consumer_key, owner_signer,
            threshold=1, shares=1,
        )
        did_doc = create_did_document(
            asset_id, access_url, owner_pk,
            ciphertext, capsule, kfrags,
        )
    except ValueError as err:
        raise DataStorageError(
            f"Failed to store data: {err}"
        ) from err

    document = {"did_document": did_doc}
    database.setdefault("collection", {})[asset_id] = document
    log.info("Stored asset %s with DID document", asset_id)


# pylint: disable=unused-argument
def consume_data(
    database: Dict[str, Any],
    data_asset_id: str,
    consumer_address: str,
    consumer_secret_key: SecretKey,
    delegating_public_key: PublicKey,
    receiving_public_key: PublicKey
) -> Tuple[bytes, str]:
    """
    Retrieve and decrypt a stored data asset.

    Args:
        database: In-memory store.
        data_asset_id: Identifier for the asset.
        consumer_address: Consumer's on-chain address
            (reserved for token-gated access).
        consumer_secret_key: Consumer's secret key.
        delegating_public_key: Owner's public key.
        receiving_public_key: Consumer's public key
            (reserved for multi-receiver support).

    Returns:
        Tuple of (decrypted bytes, access URL).

    Raises:
        DataStorageError: If asset not found.
        PermissionError: If consumer lacks access.
        DecryptionError: On decryption failure.
    """
    try:
        collection = database.get("collection", {})
        if data_asset_id not in collection:
            raise DataStorageError(
                "No encrypted data found for asset "
                f"'{data_asset_id}'."
            )

        did_doc = collection[data_asset_id]["did_document"]
        access = did_doc["access"][0]

        ciphertext = bytes.fromhex(access["data"])
        capsule = Capsule.from_bytes(
            bytes.fromhex(access["capsule"])
        )
        verified_kfrags = [
            VerifiedKeyFrag.from_verified_bytes(
                bytes.fromhex(hx)
            )
            for hx in access["kfrags"]
        ]
        cfrags = [
            reencrypt_data(capsule, vkfrag)
            for vkfrag in verified_kfrags if vkfrag
        ]

        if not cfrags:
            raise PermissionError(
                "Consumer does not have permission "
                "to access the data."
            )

        decrypted_data = decrypt_reencrypted_data(
            receiving_sk=consumer_secret_key,
            delegating_pk=delegating_public_key,
            capsule=capsule,
            verified_cfrags=cfrags,
            ciphertext=ciphertext
        )
        log.info(
            "Consumer accessed asset %s", data_asset_id
        )
        return decrypted_data, access["accessUrl"]

    except (ValueError, TypeError) as err:
        raise DecryptionError(
            f"Decryption error: {err}"
        ) from err
