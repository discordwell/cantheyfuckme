# Monetization Setup Guide

This guide explains how to set up all revenue streams for "Can They Fuck Me?"

## 1. Stripe Donation Link (Buy Me a Coffee)

The easiest way to accept donations is via Stripe Payment Links.

### Setup Steps:

1. **Create a Stripe account** at https://stripe.com if you don't have one

2. **Go to Payment Links**: https://dashboard.stripe.com/payment-links

3. **Create a new payment link**:
   - Click "Create payment link"
   - Select **"Customers choose what to pay"** for tip-jar style donations
   - Set suggested amounts: $3, $5, $10, $20
   - Product name: "Support Can They Fuck Me?" or "Buy Me a Coffee"
   - Optional: Add a product image

4. **Copy your payment link** (e.g., `https://buy.stripe.com/abc123xyz`)

5. **Update the config**:
   - Edit `frontend/src/config/stripe.ts`
   - Replace `YOUR_LINK_HERE` with your actual link
   - Set `DONATION_ENABLED = true`

```typescript
export const STRIPE_DONATION_LINK = 'https://buy.stripe.com/your_actual_link'
export const DONATION_ENABLED = true
```

6. **Rebuild and deploy**

---

## 2. Affiliate Links

Affiliate links are shown during the document analysis loading screen. These are contextual offers based on document type (insurance docs show insurance affiliates, leases show rental affiliates, etc.).

### Current Affiliate Partners (need signup):

| Partner | Document Types | Expected Payout | Signup URL |
|---------|---------------|-----------------|------------|
| **Policygenius** | Insurance | $20-120/sale | https://policygenius.com/affiliates |
| **The Zebra** | Insurance | $20-50/lead | https://thezebra.com/partners |
| **Ethos Life** | Insurance | $20-55/lead | Via Impact Radius or ShareASale |
| **LegalZoom** | Contracts | $10-30/signup | https://legalzoom.com/affiliates |
| **Rocket Lawyer** | Contracts | $10-20/signup | Via CJ Affiliate |
| **Zillow** | Leases | CPC $0.50-2 | https://zillow.com/advertising |
| **ClassPass** | Gym | $15-25/signup | Via Impact Radius |

### How to Update Affiliate Links:

1. Sign up for affiliate programs above
2. Get your unique tracking URLs
3. Edit `frontend/src/config/affiliates.ts`
4. Replace placeholder URLs with your tracking URLs

Example:
```typescript
{
  id: 'policygenius',
  name: 'Policygenius',
  // ... other fields
  url: 'https://policygenius.com/?ref=YOUR_AFFILIATE_ID',  // <-- Your tracking URL
}
```

---

## 3. Environment Variables

For the backend (if using Stripe webhooks for tracking):

```bash
# .env file in backend/
STRIPE_SECRET_KEY=sk_live_your_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
DATABASE_URL=postgresql://user:pass@host:5432/dbname
OPENAI_API_KEY=sk-your_openai_key
```

---

## Revenue Potential

Based on typical conversion rates and the high-intent audience:

| Stream | Volume | Rate | Monthly Est. |
|--------|--------|------|--------------|
| Donations | 1% of users | $5 avg | $50-500 |
| Affiliate clicks | 5% CTR | $0.50-2 CPC | $100-1000 |
| Affiliate conversions | 0.5% | $20-50 avg | $100-500 |

**Key insight**: Users analyzing insurance/legal docs are high-intent buyers, making affiliate revenue potentially lucrative.

---

## Quick Start Checklist

- [ ] Create Stripe account
- [ ] Create Payment Link for donations
- [ ] Update `frontend/src/config/stripe.ts` with your link
- [ ] Set `DONATION_ENABLED = true`
- [ ] Sign up for 2-3 affiliate programs
- [ ] Update affiliate URLs in `frontend/src/config/affiliates.ts`
- [ ] Rebuild and deploy
