# Security Policy

## Reporting a Vulnerability

If you find a security issue in this project, please report it responsibly.

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, email [edge@roguebit.me](mailto:edge@roguebit.me) with:

- Description of the vulnerability
- Steps to reproduce
- Potential impact

I'll acknowledge receipt within 48 hours and aim to provide a fix or mitigation plan within 7 days.

## Scope

This is a reference implementation meant to demonstrate proxy re-encryption patterns. It is **not** production-hardened. Known gaps are documented in the [README](README.md#known-limitations--architectural-gaps).

## Cryptographic Dependencies

| Library   | Purpose                          | Notes                                           |
|-----------|----------------------------------|-------------------------------------------------|
| PyUmbral  | Proxy re-encryption primitives   | Maintained by NuCypher / Threshold Network      |
| web3.py   | Ethereum interaction (planned)   | Used for future token-gated access               |

## Key Management Disclaimer

Key material is generated in-memory for demonstration purposes. There is no persistent key storage, HSM integration, or key rotation mechanism. See the README roadmap for planned improvements.
