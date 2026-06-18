import { describe, it, expect } from 'vitest'
import { getOffersForDocType, getRandomOffer, affiliateOffers } from './affiliates'
import { normalizeDocType, ANALYZABLE_DOC_TYPES } from '../constants/doc-types'

describe('getOffersForDocType', () => {
  it('returns category-specific offers for mapped doc types', () => {
    expect(getOffersForDocType('coi')).toBe(affiliateOffers.insurance)
    expect(getOffersForDocType('insurance_policy')).toBe(affiliateOffers.insurance)
    expect(getOffersForDocType('gym')).toBe(affiliateOffers.gym)
    expect(getOffersForDocType('employment')).toBe(affiliateOffers.employment)
    expect(getOffersForDocType('timeshare')).toBe(affiliateOffers.timeshare)
  })

  it('returns contextual offers for the five later-added doc types', () => {
    // These types were added after the original eight and were initially absent
    // from the typeMapping, so they silently fell through to the generic default
    // offers (the same under-integration that broke their analyzer routing).
    expect(getOffersForDocType('auto_purchase')).toBe(affiliateOffers.auto)
    expect(getOffersForDocType('home_improvement')).toBe(affiliateOffers.home)
    expect(getOffersForDocType('nursing_home')).toBe(affiliateOffers.legal)
    expect(getOffersForDocType('subscription')).toBe(affiliateOffers.subscription)
    expect(getOffersForDocType('debt_settlement')).toBe(affiliateOffers.debt)
  })

  it('gives every analyzable doc type a non-empty, contextual offer set', () => {
    // Coverage contract: the loading screen always has a relevant offer to show,
    // and no analyzable type quietly degrades to the generic default fallback.
    for (const docType of ANALYZABLE_DOC_TYPES) {
      const offers = getOffersForDocType(docType)
      expect(offers.length).toBeGreaterThan(0)
      expect(offers).not.toBe(affiliateOffers.default)
    }
  })

  it('falls back to default offers for unmapped or unknown types', () => {
    expect(getOffersForDocType('unknown')).toBe(affiliateOffers.default)
    expect(getOffersForDocType('contract')).toBe(affiliateOffers.default)
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

describe('affiliate offer data integrity', () => {
  const allOffers = Object.values(affiliateOffers).flat()

  it('every offer has the fields LoadingOverlay renders, all non-empty', () => {
    for (const offer of allOffers) {
      for (const field of ['id', 'name', 'tagline', 'description', 'cta', 'url'] as const) {
        expect(offer[field], `${offer.id || offer.name}.${field}`).toBeTruthy()
        expect(offer[field].trim()).not.toBe('')
      }
      expect(offer.url, `${offer.id} url`).toMatch(/^https:\/\//)
    }
  })

  it('has no duplicate offer ids across categories', () => {
    const ids = allOffers.map(o => o.id)
    expect(new Set(ids).size).toBe(ids.length)
  })
})
