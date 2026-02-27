# Mini Data Proxy

A compact reference implementation of **Proxy Re-Encryption (PRE)** for secure, multi-party data sharing — built on [PyUmbral](https://github.com/nucypher/pyUmbral/) (NuCypher / Threshold Network).

The system allows a data owner (*Alice*) to share encrypted data with a consumer (*Bob*) through a proxy (*Relayer*) — without the proxy ever seeing the plaintext and without Alice being online at the time of access.

---

## Why This Exists

Most "secure sharing" demos stop at symmetric encryption with a shared key, which sidesteps the actual hard problems: key distribution, delegation, and revocation. PRE solves these at the cryptographic layer:

- **Alice** encrypts once with her own key — no need to know Bob up front.
- **Re-encryption keys (kfrags)** let the proxy transform ciphertexts for Bob without learning anything about the plaintext or Alice's secret key.
- **Threshold scheme** (`t-of-n`) means no single proxy can act alone, limiting the blast radius of a compromised node.

This project implements the full cycle: key generation, encryption, kfrag creation, proxy re-encryption, and decryption — wired together with W3C DID documents for metadata, structured logging, and a CLI entry point.

---

## Architecture

```
┌───────────┐         kfrags          ┌───────────┐
│           │ ───────────────────────▶ │           │
│   Alice   │                         │  Relayer  │
│  (owner)  │    ciphertext + DID     │  (proxy)  │
│           │ ───────────────────────▶ │           │
└───────────┘                         └─────┬─────┘
                                            │
                                 re-encrypt │ (using kfrags)
                                            │
                                      ┌─────▼─────┐
                                      │           │
                                      │    Bob    │
                                      │ (consumer)│
                                      │           │
                                      └───────────┘
                                  decrypts with own sk
```

**Data flow:**

1. Alice generates a keypair and encrypts her data → `(ciphertext, capsule)`.
2. Alice creates *n* key fragments (kfrags) for Bob using a threshold `t-of-n` scheme and signs them.
3. Ciphertext, capsule, and kfrags are stored alongside a DID document that records access metadata.
4. When Bob requests data, the Relayer re-encrypts the capsule using `t` verified kfrags → producing capsule fragments (cfrags).
5. Bob combines `t` cfrags with his secret key to decrypt the original plaintext.

At no point does the Relayer, or any individual kfrag holder, gain access to the plaintext.

---

## Project Structure

```
.
├── main.py                  # CLI entry point (argparse)
├── src/
│   ├── config.py            # Env-driven configuration
│   ├── logger.py            # Structured logging setup
│   ├── encryption.py        # PRE primitives (encrypt, kfrags, re-encrypt, decrypt)
│   ├── database.py          # In-memory store + DID-based retrieval
│   ├── did_document.py      # W3C DID document builder
│   └── token_validation.py  # Token-burn gate (stub)
├── tests/
│   ├── test_main.py         # End-to-end CLI tests
│   ├── test_encryption.py   # Unit tests — encryption module
│   ├── test_database.py     # Unit tests — store / consume
│   └── test_did_document.py # Unit tests — DID documents
├── requirements.txt         # Core + dev dependencies
├── requirements-web3.txt    # Optional Web3 dependencies (roadmap)
├── Makefile                 # Common tasks (install, lint, test, audit)
├── SECURITY.md              # Vulnerability reporting policy
├── .editorconfig            # Editor-agnostic formatting rules
├── .pylintrc                # Pylint configuration
└── .github/
    └── workflows/
        └── ci.yml           # Lint → Test matrix → Dependency audit
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- pip

### Install & Run

```bash
git clone https://github.com/0xEB0din/refactored-mini-data-proxy.git
cd refactored-mini-data-proxy

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the full encrypt → store → consume round-trip
python main.py demo
```

Or use the `Makefile`:

```bash
make install
make demo
```

### CLI Options

```
python main.py demo --help

  --data          Plaintext payload (default: "Sample data")
  --asset-id      Unique data-asset identifier (default: asset-001)
  --access-url    URL stored in the DID document
  --threshold     Minimum kfrags for decryption (default: 2)
  --shares        Total kfrags to generate (default: 3)
```

### Run Tests

```bash
make test          # or: python -m pytest tests/ -v
make lint          # or: pylint src/
make audit         # pip-audit against known CVEs
```

---

## Configuration

All tuneable parameters are centralized in `src/config.py` and can be overridden with environment variables:

| Variable                 | Default  | Description                              |
|--------------------------|----------|------------------------------------------|
| `PRE_THRESHOLD`          | `2`      | Minimum kfrags needed for decryption     |
| `PRE_SHARES`             | `3`      | Total kfrags generated per delegation    |
| `TOKEN_BURN_REQUIRED`    | `false`  | Enable token-gated access (stub)         |
| `TOKEN_CONTRACT_ADDRESS` | `""`     | Smart contract address for token burns   |
| `LOG_LEVEL`              | `INFO`   | Python log level (DEBUG, INFO, WARNING)  |

---

## Security Model & Trust Boundaries

Understanding what the system guarantees — and where those guarantees end — is more important than the code itself.

### Trust Assumptions

| Actor | Trust Level | Assumption |
|-------|-------------|------------|
| **Alice (owner)** | Fully trusted | Holds her own secret key; generates kfrags honestly |
| **Bob (consumer)** | Trusted for his scope | Can decrypt only data explicitly delegated to him |
| **Relayer (proxy)** | Semi-trusted | Performs re-encryption faithfully, but never sees plaintext — even if compromised |
| **Network** | Untrusted | All data in transit is assumed observable (this demo has no transport security; production requires TLS/mTLS) |

The core security invariant: **a compromised proxy learns nothing about the plaintext**. The proxy holds ciphertext and kfrags, but kfrags are one-way transformation keys — they cannot be reversed to derive Alice's secret key or the plaintext.

### Threat Model

| Threat | Addressed? | How |
|--------|------------|-----|
| **Passive eavesdropping** | Yes | Data is encrypted end-to-end; proxy operates on ciphertext only |
| **Compromised proxy** | Partially | Proxy cannot decrypt; but a malicious proxy could refuse to re-encrypt (availability, not confidentiality) |
| **Kfrag substitution** | Yes | Kfrags are signed by Alice; forged or tampered fragments fail verification |
| **Collusion: proxy + Bob** | Yes | Bob can only decrypt data delegated to him; colluding with the proxy yields nothing beyond his authorized scope |
| **Collusion: proxy + external** | Yes | Kfrags without Bob's secret key are useless; re-encryption alone doesn't produce decryptable output |
| **Key compromise (Alice)** | Not addressed | No rotation/revocation mechanism — if Alice's key leaks, all her data is exposed. See roadmap. |
| **Replay attacks** | Not addressed | No nonce or timestamp validation on re-encryption requests. Relevant when this moves to a networked API. |
| **Denial of service** | Not addressed | Single-process, no rate limiting. A production proxy needs request throttling. |

**Explicitly out of scope:** side-channel attacks, implementation-level crypto bugs (delegated to PyUmbral / libsodium), physical access threats, and social engineering.

### Design Decisions

These are the architectural choices that shaped the system, along with the alternatives that were considered and why they were rejected:

**Why Proxy Re-Encryption over alternatives?**

| Approach | Considered | Rejected Because |
|----------|------------|------------------|
| **Shared symmetric key** | Yes | Requires secure key exchange for every recipient; no delegation without re-sharing |
| **Attribute-Based Encryption (ABE)** | Yes | More expressive access policies, but significantly higher computational cost and more complex key management; overkill for pairwise delegation |
| **Multi-Party Computation (MPC)** | Yes | Stronger guarantees for joint computation, but the use case is data sharing, not joint computation — MPC adds latency and protocol complexity without benefit here |
| **Proxy Re-Encryption (PRE)** | **Selected** | Right fit: Alice encrypts once, delegates per-recipient via kfrags, proxy transforms without access. Clean separation of concerns, good library support |

**Why DID documents for metadata?**

The DID structure gives each data asset a self-describing identity (`did:op:<asset-id>`) that bundles the access URL, encrypted payload, capsule, and kfrags in one document. This is forward-compatible with decentralized identity standards (W3C DID spec) and makes the system extensible — adding verifiable credentials or service endpoints requires no schema changes.

**Why threshold scheme (`t-of-n`) instead of single-kfrag?**

A single kfrag is a single point of failure — whoever holds it controls re-encryption. The threshold scheme distributes trust: you need `t` out of `n` kfrag holders to cooperate. In the current implementation, `n` kfrags go to one proxy (the Relayer), but the architecture is designed so they can be split across independent nodes without code changes.

### Input Validation Strategy

Validation is enforced at system boundaries — where data enters the system from external sources:

- **`store_data()`** — validates all parameters are non-null before any cryptographic operation
- **`create_did_document()`** — type-checks every field (PublicKey, Capsule, VerifiedKeyFrag) and rejects malformed inputs with specific error messages
- **`consume_data()`** — verifies asset existence before attempting deserialization; kfrag verification is handled by PyUmbral's `VerifiedKeyFrag` type (forged fragments raise at the library level)
- **CLI layer** — argparse enforces types (int for threshold/shares) before values reach business logic

Internal module-to-module calls trust their inputs — no redundant validation between `encryption.py` and `database.py`.

### Crypto-Shredding & Compliance

Deleting Alice's secret key renders all data encrypted under her public key permanently unrecoverable — regardless of whether the ciphertext still exists. This is **crypto-shredding**, and it's relevant for GDPR's "right to erasure": instead of hunting down every copy of the data across storage backends, you destroy the key and the data becomes cryptographic noise.

Similarly, revoking all kfrags for a specific Bob effectively cuts off his access without touching the underlying ciphertext — a clean separation between access control and data lifecycle.

---

## How Proxy Re-Encryption Works

PRE is a public-key cryptosystem that lets a semi-trusted proxy convert a ciphertext encrypted for Alice into one decryptable by Bob — without the proxy ever accessing the plaintext.

### Cryptographic Properties

| Property                  | Guarantee                                                                 |
|---------------------------|---------------------------------------------------------------------------|
| **Unidirectional**        | Re-encryption keys work in one direction only (Alice → Bob)               |
| **Non-interactive**       | Alice can delegate without Bob being online                               |
| **Non-transitive**        | Bob cannot re-delegate to a third party without Alice's involvement       |
| **Threshold**             | Requires `t-of-n` kfrags — no single proxy holds full re-encryption power|
| **CPA-secure**            | Based on the Decisional Diffie-Hellman assumption                         |

### Library Choice: PyUmbral

[PyUmbral](https://github.com/nucypher/pyUmbral/) (NuCypher) was chosen for:

- **Threshold splitting** — configurable `t-of-n` for distributed trust.
- **Signed fragments** — kfrags are signed by the delegator, preventing substitution attacks.
- **Battle-tested** — powers the Threshold Network and has been audited.
- **Clean API** — direct mapping between crypto concepts and code.

---

## CI / CD

The GitHub Actions pipeline (`.github/workflows/ci.yml`) runs three parallel jobs:

| Job       | What it does                                        |
|-----------|-----------------------------------------------------|
| **Lint**  | `pylint src/` against the project's `.pylintrc`     |
| **Test**  | `pytest tests/ -v` across Python 3.9, 3.10, 3.11   |
| **Audit** | `pip-audit` to flag known vulnerabilities in deps   |

---

## Known Limitations & Architectural Gaps

These are deliberate scope boundaries for a reference implementation — not oversights. Each one is a potential work item if this evolves toward production use.

### Security Gaps

| Gap | Risk | Mitigation Path |
|-----|------|-----------------|
| **In-memory key material** | Keys exist only in process memory, no persistence or protection | Integrate HSM / KMS (e.g., AWS KMS, HashiCorp Vault) for key wrapping |
| **No key rotation** | Compromised keys cannot be rotated without re-encrypting all data | Implement key versioning with automated re-encryption pipeline |
| **No key revocation** | Once kfrags are issued, delegation cannot be revoked | Add kfrag expiry timestamps and a revocation list checked at re-encryption time |
| **Token validation is stubbed** | `validate_token_burn()` always returns `True` | Wire up Web3 contract call to verify on-chain token burns before releasing data |
| **No TLS / mTLS** | Data in transit is not protected at the transport layer | This is an application-layer demo; wrap with HTTPS in production |

### Architectural Tradeoffs

| Tradeoff | Current Choice | Alternative |
|----------|----------------|-------------|
| **Storage** | In-memory Python dict | Persistent encrypted store (SQLCipher, Redis with encryption-at-rest) |
| **DID method** | Custom `did:op:` | Use an established DID method (did:web, did:key, did:ethr) for interoperability |
| **Threshold params** | Fixed at config time | Dynamic per-delegation policies via an access-control layer |
| **Proxy model** | Single-process, no network | Separate proxy service with REST/gRPC API |
| **Error propagation** | Custom exceptions | Structured error codes (JSON-based) for API consumers |

### Performance Considerations

- Threshold kfrag generation is O(n) — fine for small `n`, revisit for large-scale delegation graphs.
- Re-encryption is CPU-bound — a production proxy would benefit from async workers or a Rust FFI path.
- No caching of verified kfrags; repeated access re-verifies signatures each time.

---

## Roadmap

Planned improvements, roughly ordered by priority:

- [ ] **REST API layer** — FastAPI-based proxy service with OpenAPI docs
- [ ] **Token-gated access** — Web3 smart contract integration for data monetization
- [ ] **Structured audit logging** — Append-only log with tamper detection (hash chains)
- [ ] **Key lifecycle management** — HSM-backed key storage, rotation, and revocation
- [ ] **Access control policies** — ABAC/RBAC rules per data asset
- [ ] **Persistent storage backend** — Pluggable adapter (SQLCipher, IPFS, S3 with SSE)
- [ ] **Multi-party threshold proxy** — Distribute kfrags across independent proxy nodes
- [ ] **Merkle-based data integrity** — Content-addressed storage with verifiable proofs
- [ ] **Performance benchmarks** — Latency and throughput baselines for key operations
- [ ] **SonarQube / SAST integration** — Automated static analysis in CI
- [ ] **Increase test coverage** — Edge cases, negative paths, fuzzing

---

## Contributing

1. Fork the repo.
2. Create a feature branch (`git checkout -b feat/your-feature`).
3. Write tests for new functionality.
4. Ensure `make lint` and `make test` pass.
5. Open a PR with a clear description.

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

---

## License

[MIT](LICENSE)

---

Questions or feedback? Reach me on [GitHub](https://github.com/0xEB0din) or via [email](mailto:edge@roguebit.me).
