# Supported document types
SUPPORTED_DOC_TYPES = {
    "coi": {
        "name": "Certificate of Insurance",
        "description": "ACORD 25 or similar certificate of insurance",
        "supported": True
    },
    "lease": {
        "name": "Property Lease",
        "description": "Commercial or residential lease agreement",
        "supported": True
    },
    "gym_contract": {
        "name": "Gym/Fitness Membership",
        "description": "Gym or fitness center membership agreement",
        "supported": True
    },
    "employment_contract": {
        "name": "Employment Contract",
        "description": "Employment agreement, offer letter, or employee handbook",
        "supported": True
    },
    "freelancer_contract": {
        "name": "Freelancer Agreement",
        "description": "Independent contractor, freelance, or consulting agreement",
        "supported": True
    },
    "influencer_contract": {
        "name": "Influencer/Sponsorship",
        "description": "Brand deal, sponsorship, or content creator agreement",
        "supported": True
    },
    "insurance_policy": {
        "name": "Insurance Policy",
        "description": "Full insurance policy document",
        "supported": True
    },
    "timeshare_contract": {
        "name": "Timeshare Contract",
        "description": "Timeshare or vacation ownership agreement",
        "supported": True
    },
    "auto_purchase": {
        "name": "Auto Purchase Contract",
        "description": "Vehicle purchase or financing agreement",
        "supported": True
    },
    "home_improvement": {
        "name": "Home Improvement Contract",
        "description": "Contractor or home improvement agreement",
        "supported": True
    },
    "nursing_home": {
        "name": "Nursing Home Agreement",
        "description": "Nursing home or assisted living admission agreement",
        "supported": True
    },
    "subscription": {
        "name": "Subscription Agreement",
        "description": "Subscription, SaaS, or recurring service agreement",
        "supported": True
    },
    "debt_settlement": {
        "name": "Debt Settlement Agreement",
        "description": "Debt settlement, collection, or payment agreement",
        "supported": True
    },
    "contract": {
        "name": "Contract",
        "description": "General contract or agreement",
        "supported": False
    },
    "unknown": {
        "name": "Unknown Document",
        "description": "Could not identify document type",
        "supported": False
    }
}


# The classifier labels five contract types with a "_contract" suffix, but the
# rest of the system keys on the short form: the analyzer routes are
# /api/analyze-{gym,employment,freelancer,influencer,timeshare}, uploads are
# stored with those same short doc_type values, and the SPA's analyzer routing,
# disclaimer gate, state-selector gate, and affiliate mapping all switch on them.
# Canonicalize the classifier's output so a classified document can actually be
# routed. Without this, /api/classify returns e.g. "gym_contract", which matches
# no /api/analyze-* route the client knows about, so the analyze button silently
# does nothing for those five document types.
DOC_TYPE_ALIASES = {
    "gym_contract": "gym",
    "employment_contract": "employment",
    "freelancer_contract": "freelancer",
    "influencer_contract": "influencer",
    "timeshare_contract": "timeshare",
}


def canonical_doc_type(doc_type: str) -> str:
    """Map a classifier doc-type key to the canonical identifier shared by the
    analyzer endpoints, upload storage, and the SPA. Unaliased keys (most of
    them, plus ``contract``/``unknown``) pass through unchanged."""
    return DOC_TYPE_ALIASES.get(doc_type, doc_type)
