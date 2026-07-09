import { describe, it, expect } from 'vitest'
import { ANALYZABLE_DOC_TYPES, isAnalyzableDocType, normalizeDocType } from './doc-types'

describe('normalizeDocType', () => {
  // The five labels the classifier historically returned that the SPA could not
  // route. Each must collapse to the short, routable form.
  const legacyAliases: Record<string, string> = {
    gym_contract: 'gym',
    employment_contract: 'employment',
    freelancer_contract: 'freelancer',
    influencer_contract: 'influencer',
    timeshare_contract: 'timeshare',
  }

  it('maps every legacy *_contract label to its short form', () => {
    for (const [legacy, canonical] of Object.entries(legacyAliases)) {
      expect(normalizeDocType(legacy)).toBe(canonical)
    }
  })

  it('passes already-canonical types through unchanged', () => {
    for (const t of ANALYZABLE_DOC_TYPES) {
      expect(normalizeDocType(t)).toBe(t)
    }
  })

  it('passes unsupported / unknown types through unchanged', () => {
    expect(normalizeDocType('contract')).toBe('contract')
    expect(normalizeDocType('unknown')).toBe('unknown')
    expect(normalizeDocType('something_new')).toBe('something_new')
  })

  it('always normalizes into a routable doc type (the routing contract)', () => {
    // This is the invariant the original bug broke: a classified document must
    // end up as a value the analyzer routing knows about.
    for (const legacy of Object.keys(legacyAliases)) {
      expect(ANALYZABLE_DOC_TYPES).toContain(normalizeDocType(legacy))
    }
  })
})

describe('isAnalyzableDocType', () => {
  // The disclaimer gate in App.tsx queues a pending analysis only for types this
  // guard accepts, then runAnalysis routes them. These tests lock the guard to
  // the single canonical list so a new analyzer added to ANALYZABLE_DOC_TYPES
  // can never be silently dropped by a stale parallel list (the failure that
  // once no-op'd 5 of 13 analyzers).
  it('accepts every analyzable doc type', () => {
    for (const t of ANALYZABLE_DOC_TYPES) {
      expect(isAnalyzableDocType(t)).toBe(true)
    }
  })

  it('rejects non-routable classifier outputs', () => {
    // "contract"/"unknown" are valid classifier results but have no analyzer;
    // the empty string guards the "no classification yet" path.
    expect(isAnalyzableDocType('contract')).toBe(false)
    expect(isAnalyzableDocType('unknown')).toBe(false)
    expect(isAnalyzableDocType('')).toBe(false)
  })

  it('rejects legacy *_contract labels until they are normalized', () => {
    // A raw "gym_contract" is not routable; normalizeDocType must run first.
    expect(isAnalyzableDocType('gym_contract')).toBe(false)
    expect(isAnalyzableDocType(normalizeDocType('gym_contract'))).toBe(true)
  })
})
