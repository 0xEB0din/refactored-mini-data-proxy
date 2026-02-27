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
