// Friendly names for unsupported document types
export const UNSUPPORTED_DOC_NAMES: Record<string, string> = {
  'contract': 'general contracts (try uploading a specific contract type)',
  'unknown': 'this type of document',
}

// The canonical, routable document-type identifiers the SPA understands. These
// match the backend's /api/analyze-<type> routes and the doc_type values used
// for upload storage. App.tsx's runAnalysis switch, the disclaimer gate, the
// state-selector gate, and the affiliate mapping all key on these exact values.
export const ANALYZABLE_DOC_TYPES = [
  'coi',
  'lease',
  'gym',
  'employment',
  'freelancer',
  'influencer',
  'timeshare',
  'insurance_policy',
  'auto_purchase',
  'home_improvement',
  'nursing_home',
  'subscription',
  'debt_settlement',
] as const

export type AnalyzableDocType = (typeof ANALYZABLE_DOC_TYPES)[number]

// O(1) membership lookup so callers can ask "does this type have an analyzer?"
// without re-listing the identifiers. ANALYZABLE_DOC_TYPES is the single source
// of truth: adding a type there (plus its runAnalysis case) is all that's needed.
const ANALYZABLE_DOC_TYPE_SET: ReadonlySet<string> = new Set(ANALYZABLE_DOC_TYPES)

// Type guard for the routable analyzer identifiers. The disclaimer gate in
// App.tsx uses this to decide whether a classified document has an analyzer to
// run, so no parallel hand-maintained list can drift out of sync and silently
// skip the analysis (the failure mode that once hit 5 of 13 analyzers). Narrows
// a bare string to AnalyzableDocType for the pending-analysis state.
export function isAnalyzableDocType(docType: string): docType is AnalyzableDocType {
  return ANALYZABLE_DOC_TYPE_SET.has(docType)
}

// Defense in depth. The classifier's canonical output is the short form above,
// but it historically labelled five contract types with a "_contract" suffix
// the SPA cannot route ("gym_contract" matches no /api/analyze-* route), which
// made the analyze button a silent no-op for those types. Normalize them to the
// short form here so routing works regardless of which backend version answered
// /api/classify — the fix is owned by the backend, this is a belt-and-braces
// guard at the consumer boundary.
const LEGACY_DOC_TYPE_ALIASES: Record<string, string> = {
  gym_contract: 'gym',
  employment_contract: 'employment',
  freelancer_contract: 'freelancer',
  influencer_contract: 'influencer',
  timeshare_contract: 'timeshare',
}

export function normalizeDocType(docType: string): string {
  return LEGACY_DOC_TYPE_ALIASES[docType] ?? docType
}
