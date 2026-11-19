# NOTICE · GitHub-ShipGo

> This file follows the three-part structure: borrowed / original work / license. Version: 3.0.4.

## 1. Borrowed

- **Public technical facts**: Markdown tables and document structure, SHA-256 checksums, zip and CRC verification, and standard-library usage of `argparse`, `hashlib`, and `zipfile`. These are public technical facts and are not copyrightable subject matter.
- **Reference projects**: Publicly available material on skill and README authoring was read during development (see [ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md)). **Ideas and process structure only; no code, images, or prose from those sources is included.**
- **Optional dependencies**: **No third-party runtime dependencies.** The five scripts use only the Python standard library. `scripts/restyle_readme.py` imports an allowlist from `scripts/en_acceptance_check.py`, which is part of this package. No optional dependency is bundled, so no such license obligation is triggered.

## 2. Original work

- The three-stage release flow (questionnaire, automated stage, review and delivery) and its four interaction templates.
- The release manifest, the three wording rules, the 15-item closeout checklist, and the whole-package fingerprint ledger criteria.
- Five scripts under `scripts/`: manifest checking, English acceptance checking, README layout restyling, fingerprint scanning with ledger verification, and text-quality checking.
- Four script self-tests plus the four-tool joint check, with dual-source synchronization between the fingerprint probe and its handbook embedding; changing one side without the other fails the check.
- Security design: the scripts never access the network, never read credentials, and never write in place inside a delivery directory. Preflight and verification are required to run on copies; runtime residue is kept out of the package.

## 3. License

This package is **MIT** licensed; see [LICENSE](LICENSE).

- **Our obligation**: retain the copyright notice and the full license text.
- **Downstream obligation**: redistributions must likewise retain this LICENSE and the attribution in this NOTICE.
- No third-party code is bundled, so no third-party license needs to be attached.

---

The Chinese version is [NOTICE.md](NOTICE.md).
