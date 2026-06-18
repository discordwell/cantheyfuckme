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
