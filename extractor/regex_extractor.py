import re


def clean_value(value):
    """Remove noise and invalid matches"""
    if not value:
        return None

    value = value.strip()

    blacklist = [
        "STATE", "LOSS", "DESCRIPTION", "ADDRESS", "FEIN",
        "ACORD", "INSURED", "CLAIM", "DATE", "PHONE", "NUMBER", "REPORTED"
    ]

    if any(bad in value.upper() for bad in blacklist):
        return None

    if len(value) < 3:
        return None

    return value


def extract_with_regex(text):
    extracted = {}

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    # ----------------------------------------
    # POLICY NUMBER
    # ----------------------------------------
    for pattern in [
        r'Text7:\s*([A-Z0-9\-]{6,})',
        r'POLICY\s*(?:#|NO\.?|NUMBER)[:\s]+([A-Z0-9\-]{6,})',
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = clean_value(match.group(1))
            if val:
                extracted["policy_number"] = val
                break

    # ----------------------------------------
    # POLICYHOLDER NAME
    # ----------------------------------------
    for pattern in [
        r'NAME OF INSURED First Middle Last:\s*([A-Za-z][A-Za-z ,.\-]{4,}?)(?=\s+DATE OF BIRTH|\s+INSURED)',
        r'NAME\s+OF\s+INSURED[^:]*:\s*([A-Za-z][A-Za-z ,.\-]{4,})',
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = clean_value(match.group(1))
            if val:
                extracted["policyholder_name"] = val.strip()
                break

    # ----------------------------------------
    # EFFECTIVE DATES
    # ----------------------------------------
    eff_match = re.search(
        r'(?:POLICY\s+PERIOD|EFFECTIVE\s+DATE|EFF\.?\s+DATE)[:\s]*([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{2,4})',
        text, re.IGNORECASE
    )
    exp_match = re.search(
        r'(?:EXPIR\w*\s+DATE|EXP\.?\s+DATE)[:\s]*([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{2,4})',
        text, re.IGNORECASE
    )
    extracted["effective_date"] = eff_match.group(1) if eff_match else None
    extracted["expiration_date"] = exp_match.group(1) if exp_match else None

    # ----------------------------------------
    # INCIDENT DATE
    # ----------------------------------------
    for pattern in [
        r'Text3:\s*([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{2,4})',
        r'DATE OF LOSS(?:\s+AND\s+TIME)?[^:]*:\s*([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{2,4})',
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = clean_value(match.group(1))
            if val:
                extracted["incident_date"] = val
                break

    # ----------------------------------------
    # INCIDENT TIME
    # Real text: "Text4: 02:30"
    # ----------------------------------------
    time_match = re.search(r'Text4:\s*([0-9]{1,2}:[0-9]{2}(?:\s*[AP]M)?)', text, re.IGNORECASE)
    if time_match:
        extracted["incident_time"] = time_match.group(1).strip()

    # ----------------------------------------
    # LOCATION
    # ----------------------------------------
    street_match = re.search(
        r'STREET LOCATION OF LOSS:\s*(.+?)(?=\s+POLICE OR FIRE|\s+CITY STATE ZIP)',
        text, re.IGNORECASE
    )
    city_match = re.search(
        r'CITY STATE ZIP:\s*(.+?)(?=\s+COUNTRY:|\s+REPORT NUMBER)',
        text, re.IGNORECASE
    )
    if street_match and city_match:
        extracted["location"] = f"{street_match.group(1).strip()}, {city_match.group(1).strip()}"
    elif street_match:
        extracted["location"] = street_match.group(1).strip()

    # ----------------------------------------
    # DESCRIPTION
    # ----------------------------------------
    for pattern in [
        r'DESCRIPTION OF ACCIDENT ACORD[^:]*:\s*(.{20,500}?)(?=\s+VEH:|\s+NAME OF INSURED|$)',
        r'DESCRIPTION OF ACCIDENT[^:]*:\s*(.{20,500}?)(?=\s+VEH:|$)',
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            if len(val) >= 20:
                extracted["description"] = val
                break

    # ----------------------------------------
    # CLAIM TYPE
    # Negation check prevents "No injuries reported" from triggering Injury
    # ----------------------------------------
    desc_lower = text.lower()
    injury_negated = bool(re.search(
        r'no\s+injur|without\s+injur|injur\w*\s+not\s+report',
        desc_lower
    ))

    if not injury_negated and re.search(r'\binjur|bodily', desc_lower):
        extracted["claim_type"] = "Injury"
    elif "collision" in desc_lower or "collided" in desc_lower:
        extracted["claim_type"] = "Collision"
    elif "theft" in desc_lower or "stolen" in desc_lower:
        extracted["claim_type"] = "Theft"
    elif "fire" in desc_lower:
        extracted["claim_type"] = "Fire"

    # ----------------------------------------
    # ESTIMATED DAMAGE / INITIAL ESTIMATE
    # Real text: "Text45: $ 8,450.00"
    # ----------------------------------------
    for pattern in [
        r'Text45:\s*\$?\s*([0-9,]+\.[0-9]{2})',
        r'ESTIMATE\s+AMOUNT[:\s]*\$?\s*([0-9,]+\.[0-9]{2})',
        r'\$\s*([0-9,]+\.[0-9]{2})',
    ]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = clean_value(match.group(1))
            if val:
                extracted["estimated_damage"] = val
                extracted["initial_estimate"] = val
                break

    # ----------------------------------------
    # ASSET TYPE
    # Real text: "TYPE BODY: 4-Door Sedan PLATE NUMBER: ..."
    # Stops before PLATE to avoid "4-Door Sedan PLATE" bleed
    # ----------------------------------------
    asset_type_match = re.search(
        r'TYPE BODY:\s*([A-Za-z0-9 \-]+?)(?=\s+PLATE|\s+V\.I\.N|\s+[A-Z]{4,}:|\s*$)',
        text, re.IGNORECASE
    )
    if asset_type_match:
        extracted["asset_type"] = asset_type_match.group(1).strip()

    # ----------------------------------------
    # ASSET ID (VIN preferred, plate fallback)
    # ----------------------------------------
    vin_match = re.search(r'V\.?I\.?N\.?:?\s*([A-HJ-NPR-Z0-9]{17})', text, re.IGNORECASE)
    plate_match = re.search(r'PLATE NUMBER:\s*([A-Z0-9\-]{4,})', text, re.IGNORECASE)
    if vin_match:
        extracted["asset_id"] = vin_match.group(1).strip()
    elif plate_match:
        extracted["asset_id"] = plate_match.group(1).strip()

    # ----------------------------------------
    # CLAIMANT
    # Real text: "REPORTED BY: Marcus J. Holloway"
    # ----------------------------------------
    claimant_match = re.search(
        r'REPORTED BY:\s*([A-Za-z][A-Za-z ,.\-]{4,}?)(?=\s+REPORTED TO:|\s*$)',
        text, re.IGNORECASE
    )
    if claimant_match:
        val = claimant_match.group(1).strip()
        bad = ["STATE", "LOSS", "DESCRIPTION", "ADDRESS", "FEIN",
               "ACORD", "INSURED", "CLAIM", "DATE", "PHONE", "NUMBER", "REPORTED"]
        if not any(b in val.upper() for b in bad) and len(val) >= 3:
            extracted["claimant"] = val

    # ----------------------------------------
    # THIRD PARTIES
    # Real text: "NAME ADDRESSRow1: Diana Torres, 512 Congress Ave..."
    # ----------------------------------------
    third_parties = []
    for i in range(1, 5):
        tp_match = re.search(
            rf'NAME\s*ADDRESSRow{i}:\s*([A-Za-z].+?)(?=\s+PHONE AC No|\s+NAME ADDR|\s*$)',
            text, re.IGNORECASE
        )
        if tp_match:
            val = tp_match.group(1).strip()
            if len(val) > 4:
                third_parties.append(val)
    if third_parties:
        extracted["third_parties"] = third_parties

    # ----------------------------------------
    # CONTACT DETAILS
    # ----------------------------------------
    contacts = {}
    phone_match = re.search(r'PHONE CELL HOME BUS PRIMARY:\s*([\(\)0-9 \-]{10,})', text, re.IGNORECASE)
    if phone_match:
        contacts["primary_phone"] = phone_match.group(1).strip()

    email_match = re.search(r'PRIMARY EMAIL ADDRESS:\s*([\w.\-]+@[\w.\-]+)', text, re.IGNORECASE)
    if email_match:
        contacts["primary_email"] = email_match.group(1).strip()

    if contacts:
        extracted["contact_details"] = contacts

    # ----------------------------------------
    # ATTACHMENTS
    # ACORD forms don't carry attachments — mark explicitly
    # ----------------------------------------
    extracted["attachments"] = None

    return extracted