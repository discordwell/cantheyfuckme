"""Mock-mode tests for all 13 analyzer endpoints.

Each endpoint should return a well-formed report with the shared metadata
fields (document_hash, is_premium, total_issues) computed consistently.
"""
import hashlib

import pytest

GYM_TEXT = (
    "GYM MEMBERSHIP AGREEMENT. Cancellation requests must be made in person "
    "at your home club. This agreement will automatically renew for successive "
    "terms. Annual fee of $49.99 applies. Written notice via certified mail required."
)

LEASE_TEXT = (
    "COMMERCIAL LEASE AGREEMENT between Landlord Bushwick Properties LLC and "
    "Tenant. Tenant shall indemnify and hold harmless Landlord from all claims. "
    "Tenant waives subrogation. Personal guaranty required. Rent $4,500/month."
)

EMPLOYMENT_TEXT = (
    "EMPLOYMENT AGREEMENT. Employee agrees to a non-compete covenant for 24 "
    "months. All disputes resolved by binding arbitration. Employment is at-will. "
    "All inventions belong to the Company."
)

FREELANCER_TEXT = (
    "INDEPENDENT CONTRACTOR AGREEMENT. Payment net 90 days after invoice. "
    "Unlimited revisions until client satisfaction. All work product is "
    "work for hire. Client may terminate at any time without payment."
)

INFLUENCER_TEXT = (
    "SPONSORSHIP AGREEMENT. Brand receives perpetual usage rights to all "
    "content. Exclusivity for 12 months in the category. Payment net 60. "
    "Usage in perpetuity across all media."
)

TIMESHARE_TEXT = (
    "TIMESHARE PURCHASE AGREEMENT. Vacation ownership interest. Maintenance "
    "fees increase annually. Perpetuity clause binds heirs. Right of "
    "rescission within statutory period. Purchase price $25,000."
)

INSURANCE_POLICY_TEXT = (
    "HOMEOWNERS INSURANCE POLICY. Premium $1,800/year. Deductible $2,500. "
    "Exclusions: flood, earthquake, mold. Actual cash value for roof claims. "
    "Anti-concurrent causation clause applies."
)

AUTO_TEXT = (
    "RETAIL VEHICLE PURCHASE AGREEMENT. Dealer doc fee $899. GAP insurance "
    "added. Extended warranty $3,200. Financing at 14.99% APR. Mandatory "
    "binding arbitration. VIN 1HGCM82633A004352. Yo-yo financing clause."
)

HOME_IMPROVEMENT_TEXT = (
    "HOME IMPROVEMENT CONTRACT. Kitchen remodel scope. 50% deposit due at "
    "signing. Contractor may file mechanics lien. No completion date "
    "specified. Change orders at contractor discretion."
)

NURSING_HOME_TEXT = (
    "NURSING HOME ADMISSION AGREEMENT. Responsible party agrees to personal "
    "liability for all charges. Binding arbitration required. Facility may "
    "discharge resident for any reason. Third party guarantee of payment."
)

SUBSCRIPTION_TEXT = (
    "SUBSCRIPTION TERMS OF SERVICE. Plan auto-renews annually. Cancellation "
    "requires 30 days notice before renewal. No refunds for partial periods. "
    "Prices may change at any time. Recurring billing authorization."
)

DEBT_TEXT = (
    "DEBT SETTLEMENT AGREEMENT. Settlement of $4,000 on balance of $10,000. "
    "Creditor will report settled for less than full balance. Payment "
    "reactivates statute of limitations. No paid in full language."
)

COI_TEXT = (
    "CERTIFICATE OF LIABILITY INSURANCE. Insured: Test Co LLC. "
    "GL: $1,000,000 per occurrence / $2,000,000 aggregate. "
    "Additional insured box checked. Workers comp included."
)

# (path, payload, text_field, issue_keys)
ANALYZER_CASES = [
    ("/api/check-coi-compliance", {"coi_text": COI_TEXT, "state": "NY"}, "coi_text",
     ("critical_gaps", "warnings")),
    ("/api/analyze-lease", {"lease_text": LEASE_TEXT, "state": "NY"}, "lease_text",
     ("red_flags", "missing_protections")),
    ("/api/analyze-gym", {"contract_text": GYM_TEXT, "state": "CA"}, "contract_text",
     ("red_flags",)),
    ("/api/analyze-employment", {"contract_text": EMPLOYMENT_TEXT, "state": "CA", "salary": 95000},
     "contract_text", ("red_flags",)),
    ("/api/analyze-freelancer", {"contract_text": FREELANCER_TEXT, "project_value": 5000},
     "contract_text", ("red_flags", "missing_protections")),
    ("/api/analyze-influencer", {"contract_text": INFLUENCER_TEXT, "base_rate": 2000},
     "contract_text", ("red_flags",)),
    ("/api/analyze-timeshare", {"contract_text": TIMESHARE_TEXT, "state": "FL", "purchase_price": 25000},
     "contract_text", ("red_flags",)),
    ("/api/analyze-insurance-policy", {"policy_text": INSURANCE_POLICY_TEXT, "state": "TX"},
     "policy_text", ("red_flags", "coverage_gaps")),
    ("/api/analyze-auto-purchase", {"contract_text": AUTO_TEXT, "state": "CA", "vehicle_price": 32000},
     "contract_text", ("red_flags",)),
    ("/api/analyze-home-improvement", {"contract_text": HOME_IMPROVEMENT_TEXT, "state": "NY", "project_cost": 40000},
     "contract_text", ("red_flags", "missing_protections")),
    ("/api/analyze-nursing-home", {"contract_text": NURSING_HOME_TEXT, "state": "FL"},
     "contract_text", ("red_flags", "illegal_clauses")),
    ("/api/analyze-subscription", {"contract_text": SUBSCRIPTION_TEXT, "monthly_cost": 29.99},
     "contract_text", ("red_flags", "dark_patterns")),
    ("/api/analyze-debt-settlement", {"contract_text": DEBT_TEXT, "state": "TX", "debt_amount": 10000},
     "contract_text", ("red_flags", "missing_protections")),
]


@pytest.mark.parametrize(
    "path,payload,text_field,issue_keys",
    ANALYZER_CASES,
    ids=[case[0].rsplit("/", 1)[-1] for case in ANALYZER_CASES],
)
def test_analyzer_returns_finalized_report(client, path, payload, text_field, issue_keys):
    response = client.post(path, json=payload)
    assert response.status_code == 200, response.text
    body = response.json()

    expected_hash = hashlib.sha256(payload[text_field].encode("utf-8")).hexdigest()
    assert body["document_hash"] == expected_hash
    assert body["is_premium"] is False

    expected_issues = sum(len(body.get(key) or []) for key in issue_keys)
    assert body["total_issues"] == expected_issues


def test_gym_mock_flags_in_person_cancellation(client):
    response = client.post("/api/analyze-gym", json={"contract_text": GYM_TEXT, "state": "CA"})
    body = response.json()
    names = [flag["name"] for flag in body["red_flags"]]
    assert "In-Person Cancellation Only" in names
    assert body["total_issues"] >= 1


def test_analyzer_rejects_missing_text(client):
    response = client.post("/api/analyze-gym", json={"state": "CA"})
    assert response.status_code == 422
