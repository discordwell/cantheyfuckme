# Freelancer Contract Analyzer Framework

## Payment Terms Red Flags

| Issue | Detection Pattern | Risk |
|-------|------------------|------|
| Net-60+ terms | "net 60", "net 90" | HIGH |
| No late fee | Absence of penalty language | MEDIUM |
| Payment on approval | "upon satisfaction", "when approved" | HIGH |
| No milestones | Single payment for >$5K projects | MEDIUM |
| Vague triggers | "upon completion" undefined | HIGH |

### Recommended Structure
- 50% deposit on signing
- Remaining 50% on delivery (not approval)
- Late fee: 1-2% monthly
- Net-30 maximum

## Kill Fee / Cancellation

| Issue | Risk |
|-------|------|
| No kill fee | HIGH |
| Can terminate without payment | CRITICAL |
| Kill fee under 25% | MEDIUM |
| No payment for completed work | CRITICAL |

### Recommended Kill Fee Structure
| Stage | Fee |
|-------|-----|
| Before creation | 25% |
| After creation begins | 50% |
| After delivery | 75% |

## IP Ownership Red Flags

| Issue | Risk |
|-------|------|
| Automatic work-for-hire | HIGH |
| IP transfers before payment | CRITICAL |
| All rights without premium | MEDIUM |
| No portfolio rights | MEDIUM |
| Background IP included | HIGH |

### Key Distinctions
- **Assignment:** Permanent transfer (should be payment-conditioned)
- **License:** Revocable (can terminate if unpaid)
- **Work-for-hire:** Only valid for 9 statutory categories

### Always Retain
- Portfolio display rights
- Rights to preliminary/rejected concepts
- Pre-existing IP carve-out

## Scope Creep Protection

| Issue | Risk |
|-------|------|
| Unlimited revisions | CRITICAL |
| Vague deliverables | HIGH |
| No change order process | HIGH |
| "Reasonable requests" | HIGH |

### Recommended Language
- 2-3 revision rounds included
- Itemized deliverables list
- Change order for out-of-scope
- Hourly rate for additional work

## Non-Compete / Non-Solicit

| Issue | Risk |
|-------|------|
| Broad industry restriction | CRITICAL |
| Duration >12 months | HIGH |
| Undefined "competitors" | HIGH |
| Unlimited geographic scope | HIGH |

### Acceptable Terms
- Named competitors only (not "industry")
- 6-12 month maximum
- Direct solicitation only (not "accepting work")
- NDA preferred over non-compete

## Misclassification Signals

These suggest employee relationship, not contractor:

| Signal | Risk |
|--------|------|
| Fixed schedule ("9am-5pm") | HIGH |
| Tools/equipment provided | MEDIUM |
| Mandatory training | HIGH |
| Exclusivity required | HIGH |
| Indefinite duration | MEDIUM |
| "Report to" supervisor | HIGH |
| Benefits mentioned | CRITICAL |

### IRS Control Factors
1. **Behavioral:** Client dictates how/when/where
2. **Financial:** Client controls tools, expenses, payment
3. **Relationship:** Permanency, benefits, integral work
