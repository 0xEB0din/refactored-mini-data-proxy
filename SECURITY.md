# Security Policy

## Reporting a Vulnerability

If you find a security issue in this project, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, email [edge@roguebit.me](mailto:edge@roguebit.me) with:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested severity (Critical / High / Medium / Low)

I'll acknowledge receipt within 48 hours and aim to provide a fix or mitigation plan within 7 days.

## Scope

This is a reference implementation meant to demonstrate proxy re-encryption patterns. It is **not** production-hardened. Known gaps are documented in the [README](README.md#known-limitations--architectural-gaps).

## Threat Model Summary

The full threat model is in the [README](README.md#threat-model), but in short:

- **In scope:** passive eavesdropping, compromised proxy, kfrag substitution, proxy-consumer collusion
- **Out of scope:** side-channel attacks, physical access, implementation bugs in underlying crypto libraries (PyUmbral, libsodium)

## Cryptographic Dependencies

| Library     | Purpose                          | Audit Status                                    |
|-------------|----------------------------------|-------------------------------------------------|
| PyUmbral    | Proxy re-encryption primitives   | Audited; maintained by NuCypher / Threshold     |
| PyNaCl      | Low-level crypto (via PyUmbral)  | Wraps libsodium — widely audited                |
| web3.py     | Ethereum interaction (planned)   | Not used in current codebase                    |

## Key Management Disclaimer

Key material is generated in-memory for demonstration purposes. There is no persistent key storage, HSM integration, or key rotation mechanism.

**In production, you would need:**
- HSM or KMS-backed key generation and storage
- Key rotation with automated re-encryption
- Kfrag revocation with expiry timestamps
- Secure key deletion for crypto-shredding compliance

See the [README roadmap](README.md#roadmap) for planned improvements.

## Supported Versions

| Version | Supported |
|---------|-----------|
| main    | Yes       |
| < main  | No        |
