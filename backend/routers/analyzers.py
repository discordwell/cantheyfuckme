import json

from fastapi import APIRouter, HTTPException, Request
from config import MOCK_MODE, MAX_DOC_CHARS
from services.llm import llm_json_call, calculate_extraction_confidence
from services.analysis import get_doc_context, finalize_report, run_analysis
from services.db_ops import save_upload
from services.mock.coi import mock_coi_extract, mock_compliance_check
from services.mock.lease import mock_lease_analysis
from services.mock.gym import mock_gym_analysis
from services.mock.employment import mock_employment_analysis
from services.mock.freelancer import mock_freelancer_analysis
from services.mock.influencer import mock_influencer_analysis
from services.mock.timeshare import mock_timeshare_analysis
from services.mock.insurance_policy import mock_insurance_policy_analysis
from services.mock.auto_purchase import mock_auto_purchase_analysis
from services.mock.home_improvement import mock_home_improvement_analysis
from services.mock.nursing_home import mock_nursing_home_analysis
from services.mock.subscription import mock_subscription_analysis
from services.mock.debt_settlement import mock_debt_settlement_analysis

from schemas.common import (
    COIComplianceInput, ComplianceReport,
)
from schemas.lease import LeaseAnalysisInput, LeaseAnalysisReport, LeaseInsuranceClause, LeaseRedFlag
from schemas.gym import GymContractInput, GymContractReport
from schemas.employment import EmploymentContractInput, EmploymentContractReport
from schemas.freelancer import FreelancerContractInput, FreelancerContractReport
from schemas.influencer import InfluencerContractInput, InfluencerContractReport
from schemas.timeshare import TimeshareContractInput, TimeshareContractReport
from schemas.insurance_policy import InsurancePolicyInput, InsurancePolicyReport
from schemas.auto_purchase import AutoPurchaseInput, AutoPurchaseReport
from schemas.home_improvement import HomeImprovementInput, HomeImprovementReport
from schemas.nursing_home import NursingHomeInput, NursingHomeReport
from schemas.subscription import SubscriptionInput, SubscriptionReport
from schemas.debt_settlement import DebtSettlementInput, DebtSettlementReport

from prompts.coi import COI_EXTRACTION_PROMPT, COI_COMPLIANCE_PROMPT
from prompts.lease import LEASE_EXTRACTION_PROMPT, LEASE_ANALYSIS_PROMPT
from prompts.gym import GYM_ANALYSIS_PROMPT
from prompts.employment import EMPLOYMENT_ANALYSIS_PROMPT
from prompts.freelancer import FREELANCER_ANALYSIS_PROMPT
from prompts.influencer import INFLUENCER_ANALYSIS_PROMPT
from prompts.timeshare import TIMESHARE_ANALYSIS_PROMPT
from prompts.insurance_policy import INSURANCE_POLICY_ANALYSIS_PROMPT
from prompts.auto_purchase import AUTO_PURCHASE_ANALYSIS_PROMPT
from prompts.home_improvement import HOME_IMPROVEMENT_ANALYSIS_PROMPT
from prompts.nursing_home import NURSING_HOME_ANALYSIS_PROMPT
from prompts.subscription import SUBSCRIPTION_ANALYSIS_PROMPT
from prompts.debt_settlement import DEBT_SETTLEMENT_ANALYSIS_PROMPT

from data.project_types import PROJECT_TYPE_REQUIREMENTS
from data.states import (
    STATE_GYM_PROTECTIONS,
    NON_COMPETE_STATES,
    TIMESHARE_RESCISSION,
)
from data.red_flags import LEASE_RED_FLAGS, GYM_RED_FLAGS, EMPLOYMENT_RED_FLAGS

router = APIRouter(prefix="/api", tags=["analyzers"])


# ============== COI COMPLIANCE CHECK ==============

@router.post("/check-coi-compliance", response_model=ComplianceReport)
async def check_coi_compliance(input: COIComplianceInput, request: Request):
    """Check a Certificate of Insurance against contract requirements"""
    try:
        doc_hash, user, is_premium = get_doc_context(request, input.coi_text)

        # Get requirements from preset or custom
        if input.project_type and input.project_type in PROJECT_TYPE_REQUIREMENTS:
            requirements = PROJECT_TYPE_REQUIREMENTS[input.project_type]
        elif input.custom_requirements:
            requirements = input.custom_requirements
        else:
            # Default to commercial construction requirements
            requirements = PROJECT_TYPE_REQUIREMENTS["commercial_construction"]

        project_type_name = requirements.get('name', 'Commercial Construction')

        if MOCK_MODE:
            coi_data = mock_coi_extract(input.coi_text)
            result = mock_compliance_check(coi_data, requirements, input.state)
        else:
            # Step 1: Extract COI data
            coi_data = llm_json_call(COI_EXTRACTION_PROMPT.replace("<<DOCUMENT>>", input.coi_text[:MAX_DOC_CHARS]))

            # Step 2: Check compliance
            compliance_prompt = (
                COI_COMPLIANCE_PROMPT
                .replace("<<COI_DATA>>", json.dumps(coi_data, indent=2))
                .replace("<<REQUIREMENTS>>", json.dumps(requirements, indent=2))
                .replace("<<PROJECT_TYPE>>", project_type_name)
            )
            result = llm_json_call(compliance_prompt)
            result['coi_data'] = coi_data
            result['extraction_metadata'] = calculate_extraction_confidence(coi_data)

        save_upload("coi", input.coi_text, input.state, result, user_id=user.id if user else None)

        return finalize_report(
            ComplianceReport, result,
            doc_hash=doc_hash, is_premium=is_premium,
            issue_keys=("critical_gaps", "warnings"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"COI compliance check failed: {str(e)}")


# ============== LEASE ANALYSIS ==============

@router.post("/analyze-lease", response_model=LeaseAnalysisReport)
async def analyze_lease(input: LeaseAnalysisInput, request: Request):
    """Analyze a lease for insurance-related red flags and risks"""
    try:
        doc_hash, user, is_premium = get_doc_context(request, input.lease_text)

        if MOCK_MODE:
            result = mock_lease_analysis(input.lease_text, input.state)
            save_upload("lease", input.lease_text, input.state, result, user_id=user.id if user else None)
            return finalize_report(
                LeaseAnalysisReport, result,
                doc_hash=doc_hash, is_premium=is_premium,
                issue_keys=("red_flags", "missing_protections"),
            )

        # Step 1: Extract lease data
        lease_data = llm_json_call(
            LEASE_EXTRACTION_PROMPT.replace("<<DOCUMENT>>", input.lease_text[:MAX_DOC_CHARS])
        )

        # Step 2: Analyze for red flags
        analysis_prompt = (
            LEASE_ANALYSIS_PROMPT
            .replace("<<LEASE_DATA>>", json.dumps(lease_data, indent=2))
            .replace("<<RED_FLAGS>>", json.dumps(LEASE_RED_FLAGS, indent=2))
            .replace("<<STATE>>", input.state or "Not specified")
        )
        analysis = llm_json_call(analysis_prompt)

        save_upload("lease", input.lease_text, input.state, {
            "overall_risk": analysis.get("overall_risk", "medium"),
            "risk_score": analysis.get("risk_score", 50),
            "red_flags": analysis.get("red_flags", []),
        }, user_id=user.id if user else None)

        red_flags = analysis.get("red_flags", [])
        missing_protections = analysis.get("missing_protections", [])

        return LeaseAnalysisReport(
            overall_risk=analysis.get("overall_risk", "medium"),
            risk_score=analysis.get("risk_score", 50),
            lease_type=lease_data.get("lease_type", input.lease_type),
            landlord_name=lease_data.get("landlord_name"),
            tenant_name=lease_data.get("tenant_name"),
            property_address=lease_data.get("property_address"),
            lease_term=lease_data.get("lease_term"),
            insurance_requirements=[LeaseInsuranceClause(**r) for r in analysis.get("insurance_requirements", [])],
            red_flags=[LeaseRedFlag(**r) for r in red_flags],
            missing_protections=missing_protections,
            summary=analysis.get("summary", "Analysis complete."),
            negotiation_letter=analysis.get("negotiation_letter", ""),
            document_hash=doc_hash,
            is_premium=is_premium,
            total_issues=len(red_flags) + len(missing_protections)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lease analysis failed: {str(e)}")


# ============== GYM CONTRACT ANALYSIS ==============

@router.post("/analyze-gym", response_model=GymContractReport)
async def analyze_gym_contract(input: GymContractInput, request: Request):
    """Analyze a gym membership contract for red flags"""
    try:
        def build_prompt():
            state_laws = STATE_GYM_PROTECTIONS.get(input.state.upper() if input.state else "", {})
            return (
                GYM_ANALYSIS_PROMPT
                .replace("<<CONTRACT>>", input.contract_text[:MAX_DOC_CHARS])
                .replace("<<STATE>>", input.state or "Not specified")
                .replace("<<STATE_LAWS>>", json.dumps(state_laws, indent=2))
                .replace("<<RED_FLAGS>>", json.dumps(GYM_RED_FLAGS, indent=2))
            )

        return run_analysis(
            request=request,
            text=input.contract_text,
            doc_type="gym",
            report_cls=GymContractReport,
            issue_keys=("red_flags",),
            state=input.state,
            mock_fn=lambda: mock_gym_analysis(input.contract_text, input.state),
            prompt_fn=build_prompt,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gym contract analysis failed: {str(e)}")


# ============== EMPLOYMENT CONTRACT ANALYSIS ==============

@router.post("/analyze-employment", response_model=EmploymentContractReport)
async def analyze_employment_contract(input: EmploymentContractInput, request: Request):
    """Analyze an employment contract for problematic terms"""
    try:
        def build_prompt():
            state_rules = NON_COMPETE_STATES.get(input.state.upper() if input.state else "", {})
            return (
                EMPLOYMENT_ANALYSIS_PROMPT
                .replace("<<CONTRACT>>", input.contract_text[:MAX_DOC_CHARS])
                .replace("<<STATE>>", input.state or "Not specified")
                .replace("<<SALARY>>", f"${input.salary:,}" if input.salary else "Not specified")
                .replace("<<STATE_RULES>>", json.dumps(state_rules, indent=2))
                .replace("<<RED_FLAGS>>", json.dumps(EMPLOYMENT_RED_FLAGS, indent=2))
            )

        return run_analysis(
            request=request,
            text=input.contract_text,
            doc_type="employment",
            report_cls=EmploymentContractReport,
            issue_keys=("red_flags",),
            state=input.state,
            mock_fn=lambda: mock_employment_analysis(input.contract_text, input.state, input.salary),
            prompt_fn=build_prompt,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Employment contract analysis failed: {str(e)}")


# ============== FREELANCER CONTRACT ANALYSIS ==============

@router.post("/analyze-freelancer", response_model=FreelancerContractReport)
async def analyze_freelancer_contract(input: FreelancerContractInput, request: Request):
    """Analyze a freelancer/contractor agreement"""
    try:
        return run_analysis(
            request=request,
            text=input.contract_text,
            doc_type="freelancer",
            report_cls=FreelancerContractReport,
            issue_keys=("red_flags", "missing_protections"),
            mock_fn=lambda: mock_freelancer_analysis(input.contract_text, input.project_value),
            prompt_fn=lambda: FREELANCER_ANALYSIS_PROMPT.format(
                contract_text=input.contract_text[:MAX_DOC_CHARS],
                project_value=f"${input.project_value:,}" if input.project_value else "Not specified"
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Freelancer contract analysis failed: {str(e)}")


# ============== INFLUENCER CONTRACT ANALYSIS ==============

@router.post("/analyze-influencer", response_model=InfluencerContractReport)
async def analyze_influencer_contract(input: InfluencerContractInput, request: Request):
    """Analyze an influencer/sponsorship contract"""
    try:
        return run_analysis(
            request=request,
            text=input.contract_text,
            doc_type="influencer",
            report_cls=InfluencerContractReport,
            issue_keys=("red_flags",),
            mock_fn=lambda: mock_influencer_analysis(input.contract_text, input.base_rate),
            prompt_fn=lambda: INFLUENCER_ANALYSIS_PROMPT.format(
                contract_text=input.contract_text[:MAX_DOC_CHARS],
                base_rate=f"${input.base_rate:,}" if input.base_rate else "Not specified"
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Influencer contract analysis failed: {str(e)}")


# ============== TIMESHARE CONTRACT ANALYSIS ==============

@router.post("/analyze-timeshare", response_model=TimeshareContractReport)
async def analyze_timeshare_contract(input: TimeshareContractInput, request: Request):
    """Analyze a timeshare contract"""
    try:
        def build_prompt():
            rescission_info = TIMESHARE_RESCISSION.get(input.state.upper() if input.state else "", {})
            return TIMESHARE_ANALYSIS_PROMPT.format(
                contract_text=input.contract_text[:MAX_DOC_CHARS],
                state=input.state or "Not specified",
                rescission_info=json.dumps(rescission_info),
                purchase_price=f"${input.purchase_price:,}" if input.purchase_price else "Unknown",
                annual_fee=f"${input.annual_fee:,}" if input.annual_fee else "Unknown"
            )

        return run_analysis(
            request=request,
            text=input.contract_text,
            doc_type="timeshare",
            report_cls=TimeshareContractReport,
            issue_keys=("red_flags",),
            state=input.state,
            mock_fn=lambda: mock_timeshare_analysis(
                input.contract_text, input.state, input.purchase_price, input.annual_fee
            ),
            prompt_fn=build_prompt,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timeshare contract analysis failed: {str(e)}")


# ============== INSURANCE POLICY ANALYSIS ==============

@router.post("/analyze-insurance-policy", response_model=InsurancePolicyReport)
async def analyze_insurance_policy(input: InsurancePolicyInput, request: Request):
    """Analyze a consumer insurance policy"""
    try:
        return run_analysis(
            request=request,
            text=input.policy_text,
            doc_type="insurance_policy",
            report_cls=InsurancePolicyReport,
            issue_keys=("red_flags", "coverage_gaps"),
            state=input.state,
            mock_fn=lambda: mock_insurance_policy_analysis(input.policy_text, input.policy_type, input.state),
            prompt_fn=lambda: INSURANCE_POLICY_ANALYSIS_PROMPT.format(
                policy_text=input.policy_text[:MAX_DOC_CHARS],
                policy_type=input.policy_type or "Determine from text",
                state=input.state or "Not specified"
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insurance policy analysis failed: {str(e)}")


# ============== AUTO PURCHASE ANALYSIS ==============

@router.post("/analyze-auto-purchase", response_model=AutoPurchaseReport)
async def analyze_auto_purchase(input: AutoPurchaseInput, request: Request):
    """Analyze a vehicle purchase contract"""
    try:
        return run_analysis(
            request=request,
            text=input.contract_text,
            doc_type="auto_purchase",
            report_cls=AutoPurchaseReport,
            issue_keys=("red_flags",),
            state=input.state,
            mock_fn=lambda: mock_auto_purchase_analysis(
                input.contract_text, input.state, input.vehicle_price, input.trade_in_value
            ),
            prompt_fn=lambda: AUTO_PURCHASE_ANALYSIS_PROMPT.format(
                contract_text=input.contract_text[:MAX_DOC_CHARS],
                state=input.state or "Not specified",
                vehicle_price=f"${input.vehicle_price:,}" if input.vehicle_price else "Not specified",
                trade_in_value=f"${input.trade_in_value:,}" if input.trade_in_value else "Not specified"
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto purchase analysis failed: {str(e)}")


# ============== HOME IMPROVEMENT ANALYSIS ==============

@router.post("/analyze-home-improvement", response_model=HomeImprovementReport)
async def analyze_home_improvement(input: HomeImprovementInput, request: Request):
    """Analyze a home improvement / contractor contract"""
    try:
        return run_analysis(
            request=request,
            text=input.contract_text,
            doc_type="home_improvement",
            report_cls=HomeImprovementReport,
            issue_keys=("red_flags", "missing_protections"),
            state=input.state,
            mock_fn=lambda: mock_home_improvement_analysis(input.contract_text, input.state, input.project_cost),
            prompt_fn=lambda: HOME_IMPROVEMENT_ANALYSIS_PROMPT.format(
                contract_text=input.contract_text[:MAX_DOC_CHARS],
                state=input.state or "Not specified",
                project_cost=f"${input.project_cost:,}" if input.project_cost else "Not specified"
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Home improvement analysis failed: {str(e)}")


# ============== NURSING HOME ANALYSIS ==============

@router.post("/analyze-nursing-home", response_model=NursingHomeReport)
async def analyze_nursing_home(input: NursingHomeInput, request: Request):
    """Analyze a nursing home admission agreement"""
    try:
        return run_analysis(
            request=request,
            text=input.contract_text,
            doc_type="nursing_home",
            report_cls=NursingHomeReport,
            issue_keys=("red_flags", "illegal_clauses"),
            state=input.state,
            mock_fn=lambda: mock_nursing_home_analysis(input.contract_text, input.state),
            prompt_fn=lambda: NURSING_HOME_ANALYSIS_PROMPT.format(
                contract_text=input.contract_text[:MAX_DOC_CHARS],
                state=input.state or "Not specified"
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Nursing home analysis failed: {str(e)}")


# ============== SUBSCRIPTION ANALYSIS ==============

@router.post("/analyze-subscription", response_model=SubscriptionReport)
async def analyze_subscription(input: SubscriptionInput, request: Request):
    """Analyze a subscription or SaaS agreement"""
    try:
        return run_analysis(
            request=request,
            text=input.contract_text,
            doc_type="subscription",
            report_cls=SubscriptionReport,
            issue_keys=("red_flags", "dark_patterns"),
            mock_fn=lambda: mock_subscription_analysis(input.contract_text, input.monthly_cost),
            prompt_fn=lambda: SUBSCRIPTION_ANALYSIS_PROMPT.format(
                contract_text=input.contract_text[:MAX_DOC_CHARS],
                monthly_cost=f"${input.monthly_cost:,.2f}" if input.monthly_cost else "Not specified"
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subscription analysis failed: {str(e)}")


# ============== DEBT SETTLEMENT ANALYSIS ==============

@router.post("/analyze-debt-settlement", response_model=DebtSettlementReport)
async def analyze_debt_settlement(input: DebtSettlementInput, request: Request):
    """Analyze a debt settlement agreement"""
    try:
        return run_analysis(
            request=request,
            text=input.contract_text,
            doc_type="debt_settlement",
            report_cls=DebtSettlementReport,
            issue_keys=("red_flags", "missing_protections"),
            state=input.state,
            mock_fn=lambda: mock_debt_settlement_analysis(input.contract_text, input.state, input.debt_amount),
            prompt_fn=lambda: DEBT_SETTLEMENT_ANALYSIS_PROMPT.format(
                contract_text=input.contract_text[:MAX_DOC_CHARS],
                state=input.state or "Not specified",
                debt_amount=f"${input.debt_amount:,}" if input.debt_amount else "Not specified"
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debt settlement analysis failed: {str(e)}")
