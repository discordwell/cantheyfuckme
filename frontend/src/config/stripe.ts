// Stripe configuration
//
// To set up your donation link:
// 1. Go to https://dashboard.stripe.com/payment-links
// 2. Click "Create payment link"
// 3. Select "Customers choose what to pay" for donations
// 4. Set suggested amounts (e.g., $3, $5, $10)
// 5. Add a product name like "Buy Me a Coffee" or "Support Can They Fuck Me"
// 6. Copy the payment link URL and paste it below
//
// Example: https://buy.stripe.com/abc123xyz

export const STRIPE_DONATION_LINK = 'https://buy.stripe.com/cNi3cu3Kacjf2jYfbqes000'

// Set to true once you've configured your Stripe link
export const DONATION_ENABLED = true
