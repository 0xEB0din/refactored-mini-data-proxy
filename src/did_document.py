from datetime import datetime, timezone
from typing import Dict, List
from umbral import PublicKey, Capsule, VerifiedKeyFrag
from .config import DID_CONTEXT_URL, DID_METHOD
from .logger import get_logger

log = get_logger(__name__)


class InvalidKeyFrag(Exception):
    """Raised when an invalid key fragment is encountered."""


def create_did_document(
    data_asset_id: str,
    access_url: str,
    owner_public_key: PublicKey,
    ciphertext: bytes,
    capsule: Capsule,
    kfrags: List[VerifiedKeyFrag]
) -> Dict:
    """
    Create a W3C-style DID document for a data asset.

    Args:
        data_asset_id: Unique asset identifier.
        access_url: URL for data retrieval.
        owner_public_key: Owner's public key.
        ciphertext: Encrypted payload bytes.
        capsule: Capsule from the encryption step.
        kfrags: Verified key fragments for PRE.

    Returns:
        Dict representing the DID document.

    Raises:
        ValueError: If a required parameter is invalid.
        InvalidKeyFrag: If any kfrag fails validation.
    """
    try:
        _validate_inputs(
            data_asset_id, access_url,
            owner_public_key, ciphertext,
            capsule, kfrags,
        )

        did_document = {
            "@context": DID_CONTEXT_URL,
            "id": f"did:{DID_METHOD}:{data_asset_id}",
            "created": datetime.now(
                timezone.utc
            ).isoformat(),
            "access": [{
                "type": "rest",
                "accessUrl": access_url,
                "data": ciphertext.hex(),
                "capsule": bytes(capsule).hex(),
                "kfrags": [
                    bytes(kfrag).hex()
                    for kfrag in kfrags
                ],
            }],
            "encryption": {
                "type": "PyUmbral",
                "publicKey": bytes(
                    owner_public_key
                ).hex(),
            },
        }
        log.debug(
            "Created DID document: did:%s:%s",
            DID_METHOD, data_asset_id,
        )
        return did_document

    except (ValueError, InvalidKeyFrag):
        raise
    except Exception as exc:
        raise ValueError(
            f"Error creating DID document: {exc}"
        ) from exc


def _validate_inputs(
    data_asset_id, access_url, owner_public_key,
    ciphertext, capsule, kfrags
):
    """Raise on missing or mistyped parameters."""
    if not data_asset_id:
        raise ValueError("Data asset ID is missing.")
    if not access_url:
        raise ValueError("Access URL is missing.")
    if not isinstance(owner_public_key, PublicKey):
        raise ValueError("Invalid owner public key.")
    if not isinstance(ciphertext, bytes) or not ciphertext:
        raise ValueError("Invalid ciphertext.")
    if not isinstance(capsule, Capsule):
        raise ValueError("Invalid capsule.")
    if not kfrags or not all(
        isinstance(kf, VerifiedKeyFrag) for kf in kfrags
    ):
        raise InvalidKeyFrag("Invalid key fragments.")
