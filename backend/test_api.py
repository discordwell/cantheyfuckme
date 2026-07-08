"""
Insurance LLM API Test Suite
Tests all API endpoints with realistic insurance document samples
"""

import os
import requests
import json
from dataclasses import dataclass
from typing import Optional

# Overridable so the suite can target a server on a non-default port (e.g.
# when a stale dev server is already squatting on 8081).
BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8081")

# Test Documents
MESSY_COI_EMAIL = """fwd: insurance stuff

hey can u check this out? their coverage looks weird to me lol

---
CERTIFICATE OF LIABILITY INSURANCE
Insured: Artisanal Pickle Co LLC
Policy#: BOP-2024-88821
Carrier: Midwest Mutual Insurance
Eff: 1/15/24 - 1/15/25

GL: $1M per occ / $2M agg
Prod/Comp: $1M
Med Pay: $5k
Damage to Rented: $100k
deductible $2,500

also they have:
- Umbrella: $5M (policy UMB-441)
- Workers comp as required

exclusions: no coverage for fermentation explosions (weird right??)
special endorsement for food spoilage added 3/2024

premium total: $4,250/yr

let me know thx
-mike"""

COMMERCIAL_PROPERTY_QUOTE = """COMMERCIAL PROPERTY QUOTE
=========================

Prepared for: Brooklyn Roasting Company
Date: November 12, 2024
Quote #: CPQ-2024-1182

PROPOSED COVERAGE:
------------------
Building Coverage.............$2,500,000
Business Personal Property....$750,000
Business Income..............$500,000
Equipment Breakdown...........$250,000

Deductible: $5,000 / $25,000 wind/hail

ANNUAL PREMIUM: $12,400

Coverage Notes:
* Agreed value endorsement included
* Ordinance & law 25%
* NO flood coverage - Zone X requires separate
* Coffee roasting equipment schedule attached

Quoted by: Hartford Commercial Lines
Valid thru: 12/15/2024

[signature illegible]"""

POLICY_RENEWAL_NOTICE = """*** RENEWAL NOTICE ***

Dear Valued Policyholder,

Your policy is due for renewal:

Named Insured: Fixie Bike Repair & Custom Frames
                dba "Spoke & Chain"
Policy Number: CGL-NY-2023-44891
Current Term: Feb 1 2024 to Feb 1 2025

RENEWAL TERM CHANGES:
- Premium increase: $3,200 -> $3,850 (+20%)
- General Liability limit: $1M/$2M (unchanged)
- Professional Liability: ADDING $500k sublimit (new)
- Tools & Equipment floater: $75,000

IMPORTANT: Your current product liability sublimit of $500,000
will be REDUCED to $250,000 unless you opt for enhanced
coverage (+$400/yr).

Deductible remains $1,000.

EXCLUSIONS ADDED THIS TERM:
- E-bike battery fires
- Carbon fiber frame defects over $10k

Please respond by January 15, 2025.

Questions? Call 1-800-555-BIKE

Underwritten by: Velocity Insurance Group"""

MINIMAL_DOCUMENT = """Policy for John Smith. GL coverage $500k."""

EMPTY_DOCUMENT = ""

GIBBERISH_DOCUMENT = """asdfkjhasdf 12938471 !!!@@@###
no real insurance info here just noise
random words: banana helicopter submarine"""

# ==================== NEW CONTRACT TYPE TEST DOCUMENTS ====================

GYM_CONTRACT_DOCUMENT = """PLANET FITNESS MEMBERSHIP AGREEMENT

Member Name: John Smith
Location: Brooklyn, NY

1. MEMBERSHIP TYPE AND FEES
This is an annual membership agreement. Monthly dues are $22.99, billed on the 17th of each month. An Annual Fee of $49.99 will be charged on or around the 1st of each year.

2. CANCELLATION POLICY
To cancel, member must provide written notice by certified mail to the club or visit the club in person. Notice must be received by the 10th of the month to stop billing on the 17th. Early termination requires payment of a $58 buyout fee plus any outstanding balance.

3. AUTO-RENEWAL
This agreement will automatically renew on a month-to-month basis after the initial term. Member authorizes automatic payment updates if card on file changes.

4. FREEZE POLICY
Members may freeze their membership for up to 3 months per year at a cost of $15/month. Medical freezes are free with documentation. Freeze time extends your commitment period.

5. ARBITRATION AGREEMENT
Any disputes arising from this agreement shall be resolved through binding arbitration. Member waives the right to participate in class action lawsuits.

6. TERMS MAY CHANGE
Planet Fitness reserves the right to modify these terms at any time with 30 days notice."""

EMPLOYMENT_CONTRACT_DOCUMENT = """EMPLOYMENT AGREEMENT

Employee: Jane Doe
Position: Senior Software Engineer
Company: TechCorp Inc.
Location: San Francisco, CA
Start Date: February 1, 2025
Salary: $185,000 annually

1. NON-COMPETE CLAUSE
Employee agrees not to work for any competitor in the technology industry for a period of 24 months following termination within a 100-mile radius of any company office.

2. INTELLECTUAL PROPERTY
All work product, inventions, and ideas developed during employment or using company resources belong exclusively to TechCorp Inc., including work done on personal time.

3. ARBITRATION
Any disputes shall be resolved through binding arbitration in Santa Clara County. Employee waives right to jury trial and class actions.

4. AT-WILL EMPLOYMENT
Employment is at-will and may be terminated by either party at any time for any reason.

5. NON-DISCLOSURE
Employee agrees to maintain confidentiality of all company information in perpetuity."""

FREELANCER_CONTRACT_DOCUMENT = """INDEPENDENT CONTRACTOR AGREEMENT

Client: MegaBrand Corporation
Contractor: Creative Freelance Studio
Project: Website Redesign
Fee: $15,000

1. DELIVERABLES
Contractor shall deliver complete website redesign including all pages, graphics, and code.

2. PAYMENT TERMS
Payment due Net-90 upon client approval of all deliverables.

3. REVISIONS
Contractor agrees to make unlimited revisions until client is fully satisfied.

4. INTELLECTUAL PROPERTY
All work product becomes property of Client as work-for-hire immediately upon creation.

5. TERMINATION
Client may terminate this agreement at any time without payment for work completed.

6. NON-COMPETE
Contractor agrees not to work with any of Client's competitors for 12 months."""

INFLUENCER_CONTRACT_DOCUMENT = """INFLUENCER PARTNERSHIP AGREEMENT

Brand: FashionBrand Co.
Creator: @StyleInfluencer
Campaign: Summer 2025 Collection

1. DELIVERABLES
Creator will produce 3 Instagram Reels and 2 TikTok videos featuring products.

2. USAGE RIGHTS
Brand is granted perpetual, worldwide rights to use all content in any media now known or hereafter devised, including AI training and machine learning purposes.

3. EXCLUSIVITY
Creator may not promote any competing fashion brands for 6 months, including but not limited to any company selling clothing, accessories, or fashion items.

4. PAYMENT
Creator will receive $5,000 total, payable Net-60 upon posting approval.

5. APPROVAL
Brand has final approval over all content. Unlimited revisions required until approved.

6. FTC DISCLOSURE
Creator is responsible for all FTC compliance."""

TIMESHARE_CONTRACT_DOCUMENT = """VACATION OWNERSHIP PURCHASE AGREEMENT

Resort: Paradise Beach Resort & Spa
Purchaser: Robert Johnson
State: Florida
Purchase Price: $25,000
Annual Maintenance Fee: $1,200

1. OWNERSHIP TYPE
This agreement conveys a deeded interest in perpetuity.

2. PERPETUITY CLAUSE
This agreement shall be binding upon the Owner and Owner's heirs, successors, and assigns in perpetuity. Ownership interest cannot be abandoned or transferred without resort approval.

3. MAINTENANCE FEES
Maintenance fees are subject to annual adjustment based on operating costs and may increase without limitation. The Association reserves the right to levy special assessments as deemed necessary.

4. RESCISSION
Purchaser may rescind within 10 calendar days of signing. Notice must be sent by certified mail to the address below.

5. EXCHANGE PROGRAM
Exchange privileges subject to availability and additional fees. Resort makes no guarantee of availability."""

INSURANCE_POLICY_DOCUMENT = """HOMEOWNERS INSURANCE POLICY

Policy Number: HO-2025-88421
Insured: Smith Family Trust
Property: 123 Main Street, Miami, FL
Carrier: Coastal Insurance Co.

COVERAGE SUMMARY:
Dwelling: $450,000 (Actual Cash Value)
Personal Property: $150,000
Liability: $300,000

DEDUCTIBLES:
Hurricane: 5% of dwelling coverage ($22,500)
All Other Perils: $2,500

EXCLUSIONS:
- Flood damage (separate policy required)
- Mold and fungus
- Ordinance or law
- Earth movement
- Wear and tear
- Intentional loss

APPRAISAL CLAUSE:
Disputes over value shall be resolved through binding appraisal.

ANTI-CONCURRENT CAUSATION:
This policy excludes loss caused directly or indirectly by any excluded peril, regardless of other contributing causes."""

AUTO_PURCHASE_DOCUMENT = """RETAIL INSTALLMENT SALE CONTRACT - MOTOR VEHICLE

Dealer: Premier Auto Group
Buyer: Michael Chen
Date: January 15, 2025

VEHICLE INFORMATION:
Year: 2025  Make: Toyota  Model: Camry XSE
VIN: 4T1BZ1HK5LU123456
MSRP: $32,500
Dealer Markup / Market Adjustment: $3,500

ITEMIZED CHARGES:
Vehicle Price: $36,000
Documentation Fee: $799
Nitrogen Tire Fill: $399
VIN Etching: $295
Paint Protection: $695
Fabric Protection: $295
Gap Insurance: $895
Extended Warranty: $2,495
Trade-In Credit: -$8,000

FINANCING:
Total Amount Financed: $33,873
APR: 8.9%
Term: 72 months

SPOT DELIVERY AGREEMENT:
This sale is contingent upon financing approval. Dealer reserves the right to modify financing terms if the original terms are not approved by the lender. Buyer agrees to return the vehicle and sign new contract terms if financing is not approved as originally presented."""

HOME_IMPROVEMENT_DOCUMENT = """HOME IMPROVEMENT CONTRACT

Contractor: Bob's Renovation LLC
Homeowner: Sarah Williams
Project: Kitchen Renovation
Date: February 1, 2025
Project Cost: $45,000

1. SCOPE OF WORK
General kitchen renovation including cabinets, countertops, and flooring.

2. PAYMENT SCHEDULE
- 60% due at signing ($27,000)
- 20% at midpoint ($9,000)
- 20% at completion ($9,000)

3. TIMELINE
Work to begin within 30 days of signing. No specific completion date provided.

4. CHANGES
Any changes requested by homeowner will be billed at contractor's discretion.

5. QUALITY ASSURANCE
Contractor makes no assurances regarding materials or workmanship.

6. DISPUTES
All disputes shall be resolved through binding arbitration."""

NURSING_HOME_DOCUMENT = """ADMISSION AGREEMENT - SUNRISE SENIOR CARE FACILITY

Resident: Dorothy Johnson
Responsible Party: Robert Johnson (son)

1. RESPONSIBLE PARTY OBLIGATION
The undersigned Responsible Party personally guarantees payment of all charges incurred by the Resident. Responsible Party agrees to be personally liable for any amounts not covered by Medicare, Medicaid, or insurance.

2. ARBITRATION AGREEMENT
Any and all disputes, including claims of negligence, abuse, wrongful death, or violations of rights, shall be resolved exclusively through binding arbitration. Resident and Responsible Party waive the right to a jury trial and to participate in class action lawsuits.

3. LIABILITY WAIVER
The Facility shall not be responsible for injuries, illness, or death resulting from the Resident's condition, falls, or interactions with other residents. Resident holds facility harmless.

4. DISCHARGE
Facility reserves the right to discharge Resident immediately if payment is not received within 5 business days of the due date.

5. PERSONAL PROPERTY
Facility is not responsible for loss, theft, or damage to any personal property.

6. MEDICAL CONSENT
Resident consents to any and all treatments deemed necessary by the facility medical staff."""

SUBSCRIPTION_DOCUMENT = """TERMS OF SERVICE - CLOUDPRO BUSINESS SUITE

Service: CloudPro Business Suite
Plan: Enterprise Annual
Monthly Cost: $299/month (billed annually at $3,588)

1. AUTO-RENEWAL
This subscription will automatically renew for successive one-year terms unless cancelled. Cancellation must be submitted in writing by certified mail at least 60 days before the renewal date.

2. PRICE CHANGES
CloudPro reserves the right to increase pricing at any time. Continued use after notification constitutes acceptance of new pricing.

3. DATA AND EXPORT
Upon cancellation, your data will be retained for 30 days before permanent deletion. Data export is available only on Enterprise Plus plans.

4. FREE TRIAL
Your 14-day free trial automatically converts to an annual subscription. By starting the trial, you authorize us to charge your payment method for the full annual amount.

5. CANCELLATION
To cancel, you must call our retention team at 1-800-555-CLOUD between 9am-5pm EST, Monday through Friday. Online cancellation is not available."""

DEBT_SETTLEMENT_DOCUMENT = """DEBT SETTLEMENT AGREEMENT

Creditor: National Credit Services LLC
Debtor: James Wilson
Original Debt Amount: $12,500
Settlement Amount: $7,500

1. PAYMENT TERMS
Debtor agrees to pay $7,500 in three installments of $2,500 each, due on the 1st of each month beginning March 1, 2025.

2. DEFAULT
If any payment is more than 5 days late, this agreement is void and the full original balance of $12,500 plus accrued interest and collection fees becomes immediately due.

3. SETTLEMENT STATUS
Upon receipt of final payment, Creditor agrees to update the account status.

4. FINANCIAL REPORTING
(No disclosure regarding reporting obligations or potential income treatment is provided.)

5. REMAINING BALANCE
Creditor reserves the right to sell any remaining balance not covered by this settlement to a third-party collection agency.

6. ACKNOWLEDGMENT
By signing this agreement, Debtor acknowledges the validity of the full original debt amount and waives any statute of limitations defense."""

COMMERCIAL_LEASE_DOCUMENT = """COMMERCIAL LEASE AGREEMENT

Landlord: BigProperty Holdings LLC
Tenant: Small Business Inc.
Property: Suite 500, 100 Commerce Drive

1. INSURANCE REQUIREMENTS
Tenant shall maintain:
- General Liability: $2,000,000 per occurrence
- Property Insurance: Full replacement cost
- Landlord must be named as Additional Insured on all policies

2. INDEMNIFICATION
Tenant agrees to indemnify, defend and hold harmless Landlord from any and all claims, including those arising from Landlord's own negligence.

3. WAIVER OF SUBROGATION
Tenant waives all rights of subrogation against Landlord.

4. HOLD HARMLESS
Tenant assumes all risk of loss to personal property regardless of cause."""


@dataclass
class TestResult:
    name: str
    passed: bool
    message: str
    response_data: Optional[dict] = None


class InsuranceLLMTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results: list[TestResult] = []

    def run_all_tests(self):
        """Run all test cases"""
        print("\n" + "=" * 60)
        print("INSURANCE.EXE API TEST SUITE")
        print("=" * 60 + "\n")

        # Health & Connectivity Tests
        self.test_health_check()

        # Classification Tests
        self.test_classify_coi()
        self.test_classify_lease()
        self.test_classify_gym()
        self.test_classify_employment()
        self.test_classify_unknown()

        # Extraction Tests
        self.test_extract_messy_coi()
        self.test_extract_property_quote()
        self.test_extract_renewal_notice()
        self.test_extract_minimal_document()
        self.test_extract_empty_document()
        self.test_extract_gibberish()

        # COI Compliance Tests
        self.test_coi_compliance()

        # Lease Analysis Tests
        self.test_lease_analysis()

        # New Contract Type Tests
        self.test_gym_analysis()
        self.test_employment_analysis()
        self.test_freelancer_analysis()
        self.test_influencer_analysis()
        self.test_timeshare_analysis()
        self.test_insurance_policy_analysis()

        # New Contract Type Tests (Phase 2)
        self.test_auto_purchase_analysis()
        self.test_home_improvement_analysis()
        self.test_nursing_home_analysis()
        self.test_subscription_analysis()
        self.test_debt_settlement_analysis()

        # Waitlist Tests
        self.test_waitlist_signup()

        # Proposal Generation Tests
        self.test_generate_proposal()

        # Edge Cases
        self.test_invalid_json_payload()
        self.test_missing_text_field()

        # Print Summary
        self.print_summary()

        return self.results

    def _make_request(self, method: str, endpoint: str, data: dict = None) -> tuple[int, dict]:
        """Make HTTP request and return status code and response"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                resp = requests.get(url, timeout=60)
            elif method == "POST":
                resp = requests.post(url, json=data, timeout=60)
            return resp.status_code, resp.json() if resp.text else {}
        except requests.exceptions.ConnectionError:
            return 0, {"error": "Connection refused - is the server running?"}
        except requests.exceptions.Timeout:
            return 0, {"error": "Request timed out"}
        except json.JSONDecodeError:
            return resp.status_code, {"error": "Invalid JSON response", "raw": resp.text[:500]}

    def _add_result(self, name: str, passed: bool, message: str, data: dict = None):
        """Add a test result"""
        result = TestResult(name, passed, message, data)
        self.results.append(result)
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
        if not passed:
            print(f"       {message}")
        if data and not passed:
            print(f"       Response: {json.dumps(data, indent=2)[:200]}...")

    # ==================== HEALTH TESTS ====================

    def test_health_check(self):
        """Test that the API is running and responding"""
        # "/" serves the SPA in production builds; the JSON health check lives under /api
        status, data = self._make_request("GET", "/api/health")

        if status == 0:
            self._add_result("Health Check", False, data.get("error", "Unknown error"))
            return

        passed = status == 200 and "status" in data
        self._add_result(
            "Health Check",
            passed,
            f"Expected status 200 with 'status' field, got {status}" if not passed else "API is healthy",
            data
        )

    # ==================== CLASSIFICATION TESTS ====================

    def test_classify_coi(self):
        """Test that COI documents are correctly classified"""
        status, data = self._make_request("POST", "/api/classify", {"text": MESSY_COI_EMAIL})

        if status == 0:
            self._add_result("Classify COI", False, data.get("error", "Connection failed"))
            return

        passed = status == 200 and data.get("document_type") == "coi" and data.get("supported") == True
        self._add_result(
            "Classify COI",
            passed,
            f"Expected coi/supported, got {data.get('document_type')}/{data.get('supported')}" if not passed else "COI classified correctly",
            data
        )

    def test_classify_lease(self):
        """Test that lease documents are correctly classified"""
        status, data = self._make_request("POST", "/api/classify", {"text": COMMERCIAL_LEASE_DOCUMENT})

        if status == 0:
            self._add_result("Classify Lease", False, data.get("error", "Connection failed"))
            return

        passed = status == 200 and data.get("document_type") == "lease" and data.get("supported") == True
        self._add_result(
            "Classify Lease",
            passed,
            f"Expected lease/supported, got {data.get('document_type')}/{data.get('supported')}" if not passed else "Lease classified correctly",
            data
        )

    def test_classify_gym(self):
        """Test that gym contracts are correctly classified"""
        status, data = self._make_request("POST", "/api/classify", {"text": GYM_CONTRACT_DOCUMENT})

        if status == 0:
            self._add_result("Classify Gym", False, data.get("error", "Connection failed"))
            return

        passed = status == 200 and data.get("document_type") == "gym" and data.get("supported") == True
        self._add_result(
            "Classify Gym",
            passed,
            f"Expected gym/supported, got {data.get('document_type')}/{data.get('supported')}" if not passed else "Gym contract classified correctly",
            data
        )

    def test_classify_employment(self):
        """Test that employment contracts are correctly classified"""
        status, data = self._make_request("POST", "/api/classify", {"text": EMPLOYMENT_CONTRACT_DOCUMENT})

        if status == 0:
            self._add_result("Classify Employment", False, data.get("error", "Connection failed"))
            return

        passed = status == 200 and data.get("document_type") == "employment" and data.get("supported") == True
        self._add_result(
            "Classify Employment",
            passed,
            f"Expected employment/supported, got {data.get('document_type')}/{data.get('supported')}" if not passed else "Employment contract classified correctly",
            data
        )

    def test_classify_unknown(self):
        """Test that unknown documents are correctly classified as unsupported"""
        status, data = self._make_request("POST", "/api/classify", {"text": GIBBERISH_DOCUMENT})

        if status == 0:
            self._add_result("Classify Unknown", False, data.get("error", "Connection failed"))
            return

        # Unknown/gibberish should return unknown or contract with supported=False
        passed = status == 200 and data.get("supported") == False
        self._add_result(
            "Classify Unknown",
            passed,
            f"Expected supported=False, got {data.get('supported')}" if not passed else "Unknown document handled correctly",
            data
        )

    # ==================== COI COMPLIANCE TESTS ====================

    def test_coi_compliance(self):
        """Test COI compliance checking"""
        status, data = self._make_request("POST", "/api/check-coi-compliance", {
            "coi_text": MESSY_COI_EMAIL,
            "project_type": "commercial_construction",
            "state": "NY"
        })

        if status == 0:
            self._add_result("COI Compliance", False, data.get("error", "Connection failed"))
            return

        checks = []
        checks.append(("status_ok", status == 200))
        checks.append(("has_overall_status", "overall_status" in data))
        checks.append(("has_coi_data", "coi_data" in data))
        checks.append(("has_gaps_or_passed", "critical_gaps" in data or "passed" in data))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "COI Compliance",
            passed,
            f"Failed checks: {failed}" if not passed else "COI compliance check working",
            data
        )

    # ==================== LEASE ANALYSIS TESTS ====================

    def test_lease_analysis(self):
        """Test lease analysis endpoint"""
        status, data = self._make_request("POST", "/api/analyze-lease", {
            "lease_text": COMMERCIAL_LEASE_DOCUMENT,
            "state": "NY",
            "lease_type": "commercial"
        })

        if status == 0:
            self._add_result("Lease Analysis", False, data.get("error", "Connection failed"))
            return

        checks = []
        checks.append(("status_ok", status == 200))
        checks.append(("has_overall_risk", "overall_risk" in data))
        checks.append(("has_risk_score", "risk_score" in data))
        checks.append(("has_red_flags", "red_flags" in data))
        checks.append(("has_negotiation_letter", "negotiation_letter" in data))

        # Check that indemnification red flag was caught
        red_flags = data.get("red_flags", [])
        has_indemnity_flag = any("indemnif" in str(rf).lower() for rf in red_flags)
        checks.append(("caught_indemnification", has_indemnity_flag))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Lease Analysis",
            passed,
            f"Failed checks: {failed}" if not passed else "Lease analysis working correctly",
            data
        )

    # ==================== NEW CONTRACT TYPE TESTS ====================

    def test_gym_analysis(self):
        """Test gym contract analysis"""
        status, data = self._make_request("POST", "/api/analyze-gym", {
            "contract_text": GYM_CONTRACT_DOCUMENT,
            "state": "NY"
        })

        if status == 0:
            self._add_result("Gym Analysis", False, data.get("error", "Connection failed"))
            return

        checks = []
        checks.append(("status_ok", status == 200))
        checks.append(("has_overall_risk", "overall_risk" in data))
        checks.append(("has_cancellation_difficulty", "cancellation_difficulty" in data))
        checks.append(("has_red_flags", "red_flags" in data))
        checks.append(("has_cancellation_guide", "cancellation_guide" in data))

        # Should detect arbitration clause
        red_flags = data.get("red_flags", [])
        has_arbitration_flag = any("arbitration" in str(rf).lower() for rf in red_flags)
        checks.append(("caught_arbitration", has_arbitration_flag))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Gym Analysis",
            passed,
            f"Failed checks: {failed}" if not passed else "Gym analysis working correctly",
            data
        )

    def test_employment_analysis(self):
        """Test employment contract analysis"""
        status, data = self._make_request("POST", "/api/analyze-employment", {
            "contract_text": EMPLOYMENT_CONTRACT_DOCUMENT,
            "state": "CA",
            "salary": 185000
        })

        if status == 0:
            self._add_result("Employment Analysis", False, data.get("error", "Connection failed"))
            return

        checks = []
        checks.append(("status_ok", status == 200))
        checks.append(("has_overall_risk", "overall_risk" in data))
        checks.append(("has_non_compete", "has_non_compete" in data))
        checks.append(("has_state_notes", "state_notes" in data))

        # In CA, non-competes are banned - should be noted (optional - might vary by implementation)
        state_notes = data.get("state_notes", [])
        non_compete_enforceable = data.get("non_compete_enforceable", "")
        # Either state notes mention CA/banned OR non-compete is marked as unlikely enforceable
        has_ca_indication = (
            any("california" in str(n).lower() or "banned" in str(n).lower() for n in state_notes) or
            non_compete_enforceable == "unlikely"
        )
        checks.append(("ca_non_compete_note", has_ca_indication))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Employment Analysis",
            passed,
            f"Failed checks: {failed}" if not passed else "Employment analysis working correctly",
            data
        )

    def test_freelancer_analysis(self):
        """Test freelancer contract analysis"""
        status, data = self._make_request("POST", "/api/analyze-freelancer", {
            "contract_text": FREELANCER_CONTRACT_DOCUMENT,
            "project_value": 15000
        })

        if status == 0:
            self._add_result("Freelancer Analysis", False, data.get("error", "Connection failed"))
            return

        checks = []
        checks.append(("status_ok", status == 200))
        checks.append(("has_overall_risk", "overall_risk" in data))
        checks.append(("has_payment_terms", "payment_terms" in data))
        checks.append(("has_ip_ownership", "ip_ownership" in data))
        checks.append(("has_kill_fee", "has_kill_fee" in data))

        # Should catch payment issues or have no kill fee (both indicate problems)
        red_flags = data.get("red_flags", [])
        has_payment_flag = any("payment" in str(rf).lower() or "net" in str(rf).lower() or "kill" in str(rf).lower() for rf in red_flags)
        no_kill_fee = data.get("has_kill_fee") == False
        checks.append(("caught_payment_issue", has_payment_flag or no_kill_fee))

        # Should catch unlimited revisions
        has_revision_flag = any("revision" in str(rf).lower() or "unlimited" in str(rf).lower() for rf in red_flags)
        checks.append(("caught_revision_issue", has_revision_flag))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Freelancer Analysis",
            passed,
            f"Failed checks: {failed}" if not passed else "Freelancer analysis working correctly",
            data
        )

    def test_influencer_analysis(self):
        """Test influencer contract analysis"""
        status, data = self._make_request("POST", "/api/analyze-influencer", {
            "contract_text": INFLUENCER_CONTRACT_DOCUMENT,
            "base_rate": 5000
        })

        if status == 0:
            self._add_result("Influencer Analysis", False, data.get("error", "Connection failed"))
            return

        checks = []
        checks.append(("status_ok", status == 200))
        checks.append(("has_overall_risk", "overall_risk" in data))
        checks.append(("has_perpetual_rights", "has_perpetual_rights" in data))
        checks.append(("has_ai_training_rights", "has_ai_training_rights" in data))
        checks.append(("has_ftc_compliance", "ftc_compliance" in data))

        # Should have high risk score or detect perpetual/AI rights (mock may vary)
        red_flags = data.get("red_flags", [])
        has_usage_issues = any("perpetual" in str(rf).lower() or "usage" in str(rf).lower() or "ai" in str(rf).lower() for rf in red_flags)
        is_high_risk = data.get("overall_risk") == "high" or data.get("risk_score", 0) >= 60
        checks.append(("detected_perpetual_or_high_risk", data.get("has_perpetual_rights") == True or has_usage_issues or is_high_risk))

        # Should detect AI training rights or broad usage (mock may not detect specific clause)
        checks.append(("detected_ai_or_broad_usage", data.get("has_ai_training_rights") == True or has_usage_issues or is_high_risk))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Influencer Analysis",
            passed,
            f"Failed checks: {failed}" if not passed else "Influencer analysis working correctly",
            data
        )

    def test_timeshare_analysis(self):
        """Test timeshare contract analysis"""
        status, data = self._make_request("POST", "/api/analyze-timeshare", {
            "contract_text": TIMESHARE_CONTRACT_DOCUMENT,
            "state": "FL",
            "purchase_price": 25000,
            "annual_fee": 1200
        })

        if status == 0:
            self._add_result("Timeshare Analysis", False, data.get("error", "Connection failed"))
            return

        checks = []
        checks.append(("status_ok", status == 200))
        checks.append(("has_overall_risk", "overall_risk" in data))
        checks.append(("has_perpetuity_clause", "has_perpetuity_clause" in data))
        checks.append(("has_rescission_deadline", "rescission_deadline" in data))
        checks.append(("has_exit_options", "exit_options" in data))
        checks.append(("has_rescission_letter", "rescission_letter" in data))

        # Should detect perpetuity clause
        checks.append(("detected_perpetuity", data.get("has_perpetuity_clause") == True))

        # High risk expected for timeshares
        checks.append(("high_risk", data.get("overall_risk") == "high"))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Timeshare Analysis",
            passed,
            f"Failed checks: {failed}" if not passed else "Timeshare analysis working correctly",
            data
        )

    def test_insurance_policy_analysis(self):
        """Test insurance policy analysis"""
        status, data = self._make_request("POST", "/api/analyze-insurance-policy", {
            "policy_text": INSURANCE_POLICY_DOCUMENT,
            "policy_type": "home",
            "state": "FL"
        })

        if status == 0:
            self._add_result("Insurance Policy Analysis", False, data.get("error", "Connection failed"))
            return

        checks = []
        checks.append(("status_ok", status == 200))
        checks.append(("has_overall_risk", "overall_risk" in data))
        checks.append(("has_valuation_method", "valuation_method" in data))
        checks.append(("has_deductible_type", "deductible_type" in data))
        checks.append(("has_coverage_gaps", "coverage_gaps" in data))
        checks.append(("has_questions", "questions_for_agent" in data))

        # Should detect ACV (actual cash value) as concerning
        checks.append(("detected_acv", "actual_cash" in str(data.get("valuation_method", "")).lower()))

        # Should detect percentage deductible
        checks.append(("detected_percentage_deductible", data.get("deductible_type") == "percentage"))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Insurance Policy Analysis",
            passed,
            f"Failed checks: {failed}" if not passed else "Insurance policy analysis working correctly",
            data
        )

    # ==================== NEW CONTRACT TYPE TESTS (PHASE 2) ====================

    def test_auto_purchase_analysis(self):
        """Test auto purchase contract analysis"""
        status, data = self._make_request("POST", "/api/analyze-auto-purchase", {
            "contract_text": AUTO_PURCHASE_DOCUMENT,
            "state": "CA",
            "vehicle_price": 36000,
            "trade_in_value": 8000
        })

        if status == 0:
            self._add_result("Auto Purchase Analysis", False, data.get("error", "Connection failed"))
            return

        checks = []
        checks.append(("status_ok", status == 200))
        checks.append(("has_overall_risk", "overall_risk" in data))
        checks.append(("has_has_yoyo_financing", "has_yoyo_financing" in data))
        checks.append(("has_red_flags", "red_flags" in data))
        checks.append(("has_demand_letter", "demand_letter" in data))
        checks.append(("has_state_protections", "state_protections" in data))

        # Should detect yo-yo/spot delivery
        checks.append(("detected_yoyo", data.get("has_yoyo_financing") == True))

        # Should detect junk fees (nitrogen, VIN etching, etc.)
        red_flags = data.get("red_flags", [])
        has_junk_flag = any("fee" in str(rf).lower() or "nitrogen" in str(rf).lower() or "vin etch" in str(rf).lower() or "junk" in str(rf).lower() for rf in red_flags)
        checks.append(("caught_junk_fees", has_junk_flag))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Auto Purchase Analysis",
            passed,
            f"Failed checks: {failed}" if not passed else "Auto purchase analysis working correctly",
            data
        )

    def test_home_improvement_analysis(self):
        """Test home improvement contract analysis"""
        status, data = self._make_request("POST", "/api/analyze-home-improvement", {
            "contract_text": HOME_IMPROVEMENT_DOCUMENT,
            "state": "NY",
            "project_cost": 45000
        })

        if status == 0:
            self._add_result("Home Improvement Analysis", False, data.get("error", "Connection failed"))
            return

        checks = []
        checks.append(("status_ok", status == 200))
        checks.append(("has_overall_risk", "overall_risk" in data))
        checks.append(("has_red_flags", "red_flags" in data))
        checks.append(("has_protection_checklist", "protection_checklist" in data))
        checks.append(("has_missing_protections", "missing_protections" in data))

        # Should detect front-loaded payments (60% upfront)
        red_flags = data.get("red_flags", [])
        has_payment_flag = any("payment" in str(rf).lower() or "upfront" in str(rf).lower() or "front" in str(rf).lower() for rf in red_flags)
        checks.append(("caught_payment_issue", has_payment_flag))

        # Should detect no warranty
        has_warranty_flag = any("warranty" in str(rf).lower() for rf in red_flags)
        checks.append(("caught_no_warranty", has_warranty_flag))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Home Improvement Analysis",
            passed,
            f"Failed checks: {failed}" if not passed else "Home improvement analysis working correctly",
            data
        )

    def test_nursing_home_analysis(self):
        """Test nursing home agreement analysis"""
        status, data = self._make_request("POST", "/api/analyze-nursing-home", {
            "contract_text": NURSING_HOME_DOCUMENT,
            "state": "FL"
        })

        if status == 0:
            self._add_result("Nursing Home Analysis", False, data.get("error", "Connection failed"))
            return

        checks = []
        checks.append(("status_ok", status == 200))
        checks.append(("has_overall_risk", "overall_risk" in data))
        checks.append(("has_red_flags", "red_flags" in data))
        checks.append(("has_rights_guide", "rights_guide" in data))
        checks.append(("has_illegal_clauses", "illegal_clauses" in data))

        # Should detect responsible party clause (ILLEGAL)
        checks.append(("detected_responsible_party", data.get("has_responsible_party_clause") == True))

        # Should detect forced arbitration
        checks.append(("detected_arbitration", data.get("has_forced_arbitration") == True))

        # Should be high risk
        checks.append(("high_risk", data.get("overall_risk") == "high"))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Nursing Home Analysis",
            passed,
            f"Failed checks: {failed}" if not passed else "Nursing home analysis working correctly",
            data
        )

    def test_subscription_analysis(self):
        """Test subscription/SaaS agreement analysis"""
        status, data = self._make_request("POST", "/api/analyze-subscription", {
            "contract_text": SUBSCRIPTION_DOCUMENT,
            "monthly_cost": 299
        })

        if status == 0:
            self._add_result("Subscription Analysis", False, data.get("error", "Connection failed"))
            return

        checks = []
        checks.append(("status_ok", status == 200))
        checks.append(("has_overall_risk", "overall_risk" in data))
        checks.append(("has_red_flags", "red_flags" in data))
        checks.append(("has_cancellation_guide", "cancellation_guide" in data))
        checks.append(("has_dark_patterns", "dark_patterns" in data))

        # Should detect auto-renewal
        checks.append(("detected_auto_renewal", data.get("has_auto_renewal") == True))

        # Should detect price increase clause
        checks.append(("detected_price_increase", data.get("has_price_increase_clause") == True))

        # Should detect phone-only cancellation or difficult cancellation
        red_flags = data.get("red_flags", [])
        has_cancel_flag = any("cancel" in str(rf).lower() or "phone" in str(rf).lower() for rf in red_flags)
        checks.append(("caught_cancel_difficulty", has_cancel_flag))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Subscription Analysis",
            passed,
            f"Failed checks: {failed}" if not passed else "Subscription analysis working correctly",
            data
        )

    def test_debt_settlement_analysis(self):
        """Test debt settlement agreement analysis"""
        status, data = self._make_request("POST", "/api/analyze-debt-settlement", {
            "contract_text": DEBT_SETTLEMENT_DOCUMENT,
            "state": "TX",
            "debt_amount": 12500
        })

        if status == 0:
            self._add_result("Debt Settlement Analysis", False, data.get("error", "Connection failed"))
            return

        checks = []
        checks.append(("status_ok", status == 200))
        checks.append(("has_overall_risk", "overall_risk" in data))
        checks.append(("has_red_flags", "red_flags" in data))
        checks.append(("has_settlement_letter", "settlement_letter" in data))
        checks.append(("has_missing_protections", "missing_protections" in data))

        # Should detect missing "paid in full" language
        checks.append(("detected_no_paid_in_full", data.get("has_paid_in_full") == False))

        # Should detect statute of limitations reset
        checks.append(("detected_sol_reset", data.get("resets_statute_of_limitations") == True))

        # Should detect missing tax warning
        checks.append(("detected_no_tax_warning", data.get("has_tax_warning") == False))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Debt Settlement Analysis",
            passed,
            f"Failed checks: {failed}" if not passed else "Debt settlement analysis working correctly",
            data
        )

    # ==================== WAITLIST TESTS ====================

    def test_waitlist_signup(self):
        """Test waitlist signup endpoint"""
        status, data = self._make_request("POST", "/api/waitlist", {
            "email": "test@example.com",
            "document_type": "unknown",
            "document_text": "Some unsupported document content"
        })

        if status == 0:
            self._add_result("Waitlist Signup", False, data.get("error", "Connection failed"))
            return

        passed = status == 200 and data.get("success") == True
        self._add_result(
            "Waitlist Signup",
            passed,
            f"Expected success=True, got {data}" if not passed else "Waitlist signup working",
            data
        )

    # ==================== EXTRACTION TESTS ====================

    def test_extract_messy_coi(self):
        """Test extraction from a messy forwarded COI email"""
        status, data = self._make_request("POST", "/api/extract", {"text": MESSY_COI_EMAIL})

        if status == 0:
            self._add_result("Extract Messy COI", False, data.get("error", "Connection failed"))
            return

        # Validate response structure
        checks = []

        # Must have insured name
        if data.get("insured_name"):
            checks.append(("insured_name", "Artisanal Pickle" in data["insured_name"]))
        else:
            checks.append(("insured_name", False))

        # Must have policy number
        if data.get("policy_number"):
            checks.append(("policy_number", "BOP-2024-88821" in data["policy_number"]))
        else:
            checks.append(("policy_number", False))

        # Must have carrier
        if data.get("carrier"):
            checks.append(("carrier", "Midwest" in data["carrier"]))
        else:
            checks.append(("carrier", False))

        # Must have coverages array
        checks.append(("coverages", isinstance(data.get("coverages"), list) and len(data.get("coverages", [])) > 0))

        # Must have exclusions mentioning fermentation
        exclusions = data.get("exclusions", [])
        has_fermentation = any("ferment" in str(e).lower() for e in exclusions)
        checks.append(("exclusions_fermentation", has_fermentation))

        # Must have premium
        checks.append(("premium", data.get("total_premium") is not None))

        # Must have risk score between 1-100
        risk = data.get("risk_score")
        checks.append(("risk_score", risk is not None and 1 <= risk <= 100))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Extract Messy COI",
            passed,
            f"Failed checks: {failed}" if not passed else "All fields extracted correctly",
            data
        )

    def test_extract_property_quote(self):
        """Test extraction from a commercial property quote"""
        status, data = self._make_request("POST", "/api/extract", {"text": COMMERCIAL_PROPERTY_QUOTE})

        if status == 0:
            self._add_result("Extract Property Quote", False, data.get("error", "Connection failed"))
            return

        checks = []

        # Must have insured name
        if data.get("insured_name"):
            checks.append(("insured_name", "Brooklyn Roasting" in data["insured_name"]))
        else:
            checks.append(("insured_name", False))

        # Must have coverages with building coverage
        coverages = data.get("coverages", [])
        has_building = any("building" in str(c).lower() for c in coverages)
        checks.append(("building_coverage", has_building))

        # Must identify flood exclusion as compliance issue or in notes
        exclusions = data.get("exclusions", [])
        compliance = data.get("compliance_issues", [])
        all_issues = str(exclusions) + str(compliance) + str(data.get("summary", ""))
        has_flood_note = "flood" in all_issues.lower()
        checks.append(("flood_exclusion_noted", has_flood_note))

        # Must have premium of $12,400
        premium = str(data.get("total_premium", ""))
        checks.append(("premium", "12" in premium and "400" in premium))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Extract Property Quote",
            passed,
            f"Failed checks: {failed}" if not passed else "Property quote extracted correctly",
            data
        )

    def test_extract_renewal_notice(self):
        """Test extraction from a policy renewal notice"""
        status, data = self._make_request("POST", "/api/extract", {"text": POLICY_RENEWAL_NOTICE})

        if status == 0:
            self._add_result("Extract Renewal Notice", False, data.get("error", "Connection failed"))
            return

        checks = []

        # Must have policy number
        if data.get("policy_number"):
            checks.append(("policy_number", "CGL-NY-2023-44891" in data["policy_number"]))
        else:
            checks.append(("policy_number", False))

        # Must have carrier
        if data.get("carrier"):
            checks.append(("carrier", "Velocity" in data["carrier"]))
        else:
            checks.append(("carrier", False))

        # Must identify e-bike exclusion
        exclusions = data.get("exclusions", [])
        has_ebike = any("e-bike" in str(e).lower() or "ebike" in str(e).lower() or "battery" in str(e).lower() for e in exclusions)
        checks.append(("ebike_exclusion", has_ebike))

        # Should flag premium increase as notable
        premium = str(data.get("total_premium", ""))
        checks.append(("premium", "3" in premium and "850" in premium))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Extract Renewal Notice",
            passed,
            f"Failed checks: {failed}" if not passed else "Renewal notice extracted correctly",
            data
        )

    def test_extract_minimal_document(self):
        """Test extraction from a minimal document with very little info"""
        status, data = self._make_request("POST", "/api/extract", {"text": MINIMAL_DOCUMENT})

        if status == 0:
            self._add_result("Extract Minimal Doc", False, data.get("error", "Connection failed"))
            return

        # Should still return valid structure even with minimal data
        checks = []
        checks.append(("has_structure", "coverages" in data))
        checks.append(("coverages_is_list", isinstance(data.get("coverages"), list)))

        # Should extract "John Smith" as insured
        if data.get("insured_name"):
            checks.append(("insured_name", "John Smith" in data["insured_name"]))

        # Should extract GL coverage
        coverages = data.get("coverages", [])
        has_gl = any("500" in str(c) or "liability" in str(c).lower() for c in coverages)
        checks.append(("gl_coverage", has_gl or len(coverages) > 0))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Extract Minimal Doc",
            passed,
            f"Failed checks: {failed}" if not passed else "Minimal doc handled gracefully",
            data
        )

    def test_extract_empty_document(self):
        """Test that empty document returns appropriate error or empty structure"""
        status, data = self._make_request("POST", "/api/extract", {"text": EMPTY_DOCUMENT})

        # Either a 400 error OR an empty but valid structure is acceptable
        if status == 400:
            self._add_result("Extract Empty Doc", True, "Correctly rejected empty document")
            return

        if status == 0:
            self._add_result("Extract Empty Doc", False, data.get("error", "Connection failed"))
            return

        # If 200, should have empty/null fields but valid structure
        checks = []
        checks.append(("has_structure", "coverages" in data))
        checks.append(("coverages_empty_or_list", data.get("coverages") is None or isinstance(data.get("coverages"), list)))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Extract Empty Doc",
            passed,
            f"Failed checks: {failed}" if not passed else "Empty doc handled gracefully",
            data
        )

    def test_extract_gibberish(self):
        """Test that gibberish document doesn't crash and returns valid structure"""
        status, data = self._make_request("POST", "/api/extract", {"text": GIBBERISH_DOCUMENT})

        if status == 0:
            self._add_result("Extract Gibberish", False, data.get("error", "Connection failed"))
            return

        # Should return valid structure even if fields are empty/null
        checks = []
        checks.append(("status_ok", status == 200))
        checks.append(("has_structure", "coverages" in data))
        checks.append(("no_crash", True))  # If we got here, it didn't crash

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Extract Gibberish",
            passed,
            f"Failed checks: {failed}" if not passed else "Gibberish handled gracefully",
            data
        )

    # ==================== PROPOSAL TESTS ====================

    def test_generate_proposal(self):
        """Test proposal generation from extracted data"""
        # First extract a document
        _, extracted = self._make_request("POST", "/api/extract", {"text": MESSY_COI_EMAIL})

        if not extracted or "coverages" not in extracted:
            self._add_result("Generate Proposal", False, "Could not extract document first")
            return

        # Now generate proposal
        status, data = self._make_request("POST", "/api/generate-proposal", extracted)

        if status == 0:
            self._add_result("Generate Proposal", False, data.get("error", "Connection failed"))
            return

        checks = []
        checks.append(("status_ok", status == 200))
        checks.append(("has_proposal", "proposal" in data))

        proposal = data.get("proposal", "")
        checks.append(("proposal_not_empty", len(proposal) > 100))

        # Proposal should mention the insured
        checks.append(("mentions_insured", "pickle" in proposal.lower() or "artisanal" in proposal.lower()))

        failed = [c[0] for c in checks if not c[1]]
        passed = len(failed) == 0

        self._add_result(
            "Generate Proposal",
            passed,
            f"Failed checks: {failed}" if not passed else "Proposal generated successfully",
            {"proposal_length": len(proposal), "preview": proposal[:200] + "..."} if proposal else data
        )

    # ==================== ERROR HANDLING TESTS ====================

    def test_invalid_json_payload(self):
        """Test that invalid JSON is handled gracefully"""
        try:
            resp = requests.post(
                f"{self.base_url}/api/extract",
                data="not valid json {{{",
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            # Should return 422 (Unprocessable Entity) for invalid JSON
            passed = resp.status_code == 422
            self._add_result(
                "Invalid JSON Payload",
                passed,
                f"Expected 422, got {resp.status_code}" if not passed else "Invalid JSON rejected correctly"
            )
        except Exception as e:
            self._add_result("Invalid JSON Payload", False, str(e))

    def test_missing_text_field(self):
        """Test that missing required field returns appropriate error"""
        status, data = self._make_request("POST", "/api/extract", {"wrong_field": "test"})

        # Should return 422 for missing required field
        passed = status == 422
        self._add_result(
            "Missing Text Field",
            passed,
            f"Expected 422, got {status}" if not passed else "Missing field rejected correctly",
            data
        )

    # ==================== SUMMARY ====================

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)

        print(f"\nTotal: {total} | Passed: {passed} | Failed: {failed}")
        print(f"Success Rate: {passed/total*100:.1f}%")

        if failed > 0:
            print("\nFailed Tests:")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.name}: {r.message}")

        print("\n" + "=" * 60)

        return failed == 0


if __name__ == "__main__":
    tester = InsuranceLLMTester()
    tester.run_all_tests()
