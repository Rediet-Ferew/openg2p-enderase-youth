# OpenG2P Enderase Youth Registry

Odoo addons for the Enderase Youth registry.

## Addons

### g2p_enderase_youth_registry

Registry module for Enderase youth members and groups. It builds on the OpenG2P social registry and uses `res.partner` as the canonical registry record.

## Dependency

This module depends on:

- `g2p_social_registry`

It does not depend on the ATI farmer registry. The farmer profile was used only as an implementation reference.

## Registry Model

The registry supports:

- Individuals: youth members, beneficiaries, representatives
- Groups: startups, collectives, communities, associations, organizations

A startup is treated as a type of group.

## Installation

Ensure this repository is included in `addons_path`, for example:

```text
custom_addons/openg2p-enderase-youth