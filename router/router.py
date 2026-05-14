def route_claim(validation):
    fields = validation.get("fields", {})
    missing = validation.get("missing_fields", [])
    description = fields.get("description", "") or ""
    claim_type = fields.get("claim_type", "") or ""
    estimated_damage = fields.get("estimated_damage", "") or ""

    # Convert estimated damage string to float for comparison
    damage_amount = None
    try:
        damage_amount = float(estimated_damage.replace(",", ""))
    except (ValueError, AttributeError):
        pass

    # Rule 1: Fraud / investigation keywords
    fraud_keywords = ["fraud", "inconsistent", "staged", "suspicious", "fabricated"]
    if any(kw in description.lower() for kw in fraud_keywords):
        return {
            "route": "Investigation Flag",
            "reason": "Description contains suspicious keywords indicating possible fraud."
        }

    # Rule 2: Injury claim → Specialist Queue
    if claim_type.lower() == "injury":
        return {
            "route": "Specialist Queue",
            "reason": "Claim type is Injury — requires specialist handling."
        }

    # Rule 3: Missing mandatory fields → Manual Review
    if missing:
        return {
            "route": "Manual Review",
            "reason": f"Mandatory fields missing: {', '.join(missing)}."
        }

    # Rule 4: Damage < 25,000 → Fast-track
    if damage_amount is not None and damage_amount < 25000:
        return {
            "route": "Fast-track",
            "reason": f"Estimated damage ${damage_amount:,.2f} is below the $25,000 threshold."
        }

    # Rule 5: Damage >= 25,000 → Standard Review
    return {
        "route": "Standard Review",
        "reason": f"Estimated damage ${damage_amount:,.2f} meets or exceeds the $25,000 threshold."
    }