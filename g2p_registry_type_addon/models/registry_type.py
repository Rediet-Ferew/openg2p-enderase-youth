from enum import Enum


class G2PTargetModelMapping:
    """Static mapping from PBMS registry type key to Odoo model name."""

    MODEL_MAPPING = {
        "household": "g2p.household.registry",
        "individual": "g2p.individual.registry",
        "youth": "g2p.youth.registry",
    }
    IDENTIFIER_FIELD_MAPPING = {
        "household": "internal_record_id",
        "individual": "internal_record_id",
        "youth": "internal_record_id",
    }

    @classmethod
    def get_target_model_name(cls, key):
        """Get the target Odoo model name for a registry type key."""
        return cls.MODEL_MAPPING.get(key)

    @classmethod
    def get_target_identifier_field(cls, key):
        """Get the registry identifier field selected by PBMS rules."""
        return cls.IDENTIFIER_FIELD_MAPPING.get(key, "internal_record_id")


class G2PRegistryType(Enum):
    HOUSEHOLD = "household"
    INDIVIDUAL = "individual"
    YOUTH = "youth"
    OTHER = "other"

    @classmethod
    def selection(cls):
        """Return Odoo selection tuples for configured PBMS registries."""
        return [(member.value, member.name.replace("_", " ").title()) for member in cls]
