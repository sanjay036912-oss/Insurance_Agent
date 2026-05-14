MANDATORY_FIELDS = [
    "policy_number",
    "policyholder_name",
    "incident_date",
    "incident_time",
    "location",
    "description",
    "claimant",
    "claim_type",
    "estimated_damage",
    "initial_estimate",
    "asset_type",
    "asset_id",
    "contact_details",
]

# These are expected to be absent in basic ACORD forms — don't flag as missing
OPTIONAL_FIELDS = [
    "effective_date",
    "expiration_date",
    "third_parties",
    "attachments",
]


def validate_fields(fields):
    missing = []

    for field in MANDATORY_FIELDS:
        value = fields.get(field)
        # Consider None, empty string, or empty dict as missing
        if value is None or value == "" or value == {}:
            missing.append(field)

    return {
        "fields": fields,
        "missing_fields": missing,
        "is_complete": len(missing) == 0
    }