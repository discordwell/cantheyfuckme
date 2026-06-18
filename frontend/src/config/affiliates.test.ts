import { describe, it, expect } from 'vitest'
import { getOffersForDocType, getRandomOffer, affiliateOffers } from './affiliates'
import { normalizeDocType } from '../constants/doc-types'

describe('getOffersForDocType', () => {
  it('returns category-specific offers for mapped doc types', () => {
    expect(getOffersForDocType('coi')).toBe(affiliateOffers.insurance)
    expect(getOffersForDocType('insurance_policy')).toBe(affiliateOffers.insurance)
    expect(getOffersForDocType('gym')).toBe(affiliateOffers.gym)
    expect(getOffersForDocType('employment')).toBe(affiliateOffers.employment)
    expect(getOffersForDocType('timeshare')).toBe(affiliateOffers.timeshare)
  })

  it('falls back to default offers for unmapped or unknown types', () => {
    expect(getOffersForDocType('unknown')).toBe(affiliateOffers.default)
    expect(getOffersForDocType('auto_purchase')).toBe(affiliateOffers.default)
  })

  it('serves the right offers after normalizing a legacy classifier label', () => {
    // Before the doc-type fix, "gym_contract" fell through to default offers
    // because it was not in the typeMapping. Normalizing first restores the
    // fitness-specific offers.
    expect(getOffersForDocType(normalizeDocType('gym_contract'))).toBe(affiliateOffers.gym)
    expect(getOffersForDocType(normalizeDocType('timeshare_contract'))).toBe(affiliateOffers.timeshare)
  })
})

describe('getRandomOffer', () => {
  it('returns an offer drawn from that doc type’s set', () => {
    const offer = getRandomOffer('gym')
    expect(affiliateOffers.gym).toContain(offer)
  })
})
