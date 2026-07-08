import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
import stripe
from config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from services.auth import (get_current_user, add_credits_to_user, use_credit,
                           check_premium_access, get_user_by_email)
from schemas.auth import CheckoutInput, UnlockInput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["payments"])


@router.post("/create-checkout-session")
def create_checkout_session(input: CheckoutInput, request: Request):
    """Create a Stripe checkout session for purchasing credits"""
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Must be logged in to purchase")

    try:
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "Full Report Unlock",
                            "description": "Unlock the complete detailed analysis report"
                        },
                        "unit_amount": 300,  # $3.00 in cents
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=input.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=input.cancel_url,
            metadata={
                "user_id": str(user.id),
                "document_hash": input.document_hash
            }
        )

        return {"checkout_url": checkout_session.url, "session_id": checkout_session.id}

    except Exception as e:
        logger.error("Stripe error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/stripe-webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events.

    Stays ``async def`` (unlike the rest of the API) because signature
    verification needs the raw body, which only ``await request.body()``
    provides; the blocking DB work below hops to the threadpool instead.
    """
    if not STRIPE_SECRET_KEY or not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Stripe not configured")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle checkout.session.completed
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})

        user_id = metadata.get("user_id")
        document_hash = metadata.get("document_hash")

        if user_id and document_hash:
            # Add credit and unlock document. Run off the event loop: this is
            # an async endpoint, and these helpers do blocking DB round-trips.
            def grant_unlock():
                add_credits_to_user(int(user_id), 1)
                use_credit(int(user_id), document_hash)

            await run_in_threadpool(grant_unlock)
            logger.info("Unlocked document %s for user %s", document_hash, user_id)

    return {"received": True}


@router.post("/unlock-report")
def unlock_report(input: UnlockInput, request: Request):
    """Use a credit to unlock a report (for users with existing credits)"""
    document_hash = input.document_hash

    if not document_hash:
        raise HTTPException(status_code=400, detail="document_hash required")

    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Must be logged in")

    # Check if already unlocked
    if check_premium_access(user.id, document_hash):
        return {"success": True, "message": "Already unlocked", "credits": user.credits}

    # Try to use a credit
    if use_credit(user.id, document_hash):
        # Refresh user to get updated credits
        refreshed_user = get_user_by_email(user.email)
        return {
            "success": True,
            "message": "Report unlocked",
            "credits": refreshed_user.credits if refreshed_user else user.credits - 1
        }
    else:
        raise HTTPException(status_code=402, detail="No credits available. Please purchase more.")


@router.get("/check-unlock/{document_hash}")
def check_unlock(document_hash: str, request: Request):
    """Check if user has unlocked a specific document"""
    user = get_current_user(request)
    if not user:
        return {"unlocked": False, "authenticated": False}

    unlocked = check_premium_access(user.id, document_hash)
    return {"unlocked": unlocked, "authenticated": True, "credits": user.credits}
