// Shape of the /api/ocr response. The page fields are present for real
// extractions (PDF + image); the mock-mode placeholder omits them, so they are
// optional and consumers must treat their absence as "no page information".
export interface OcrResult {
  text: string
  total_pages?: number
  pages_processed?: number
  truncated?: boolean
}

// Shown when the upload never reached the server (fetch throws a TypeError) or
// failed in a way the backend didn't explain — in local dev that usually means
// the API isn't up.
export const OCR_BACKEND_DOWN_MESSAGE =
  'Failed to process file. Make sure the backend is running!'

/**
 * Turn whatever the OCR upload flow threw into the message to alert the user.
 *
 * The backend rejects the fixable cases with an actionable 4xx `detail` — a
 * corrupt or password-protected PDF, an unsupported file type, a too-large
 * upload, or a rate-limit 429 — which the caller re-throws as an Error carrying
 * that text; surface it verbatim so the user knows exactly what to fix. A
 * TypeError from fetch (or any error without a message) instead means the
 * request never reached the server, so we point at the backend. Mirrors the
 * error handling in useAnalyzer so every upload path reads the server's reason.
 */
export function formatOcrError(err: unknown): string {
  // Check TypeError before Error: a network failure is a TypeError (a subclass
  // of Error) but carries an opaque message like "Failed to fetch", not a reason
  // the user can act on.
  if (err instanceof TypeError) return OCR_BACKEND_DOWN_MESSAGE
  if (err instanceof Error && err.message) return err.message
  return OCR_BACKEND_DOWN_MESSAGE
}

/**
 * Build a user-facing warning when OCR processed only the first N pages of a
 * longer PDF. Returns null when nothing was dropped (or the response lacks page
 * counts), so the caller can render the banner only when there is something to
 * say. The point is that the analysis below is partial — clauses on the dropped
 * pages (often the arbitration / indemnification / auto-renew traps that live in
 * the back) will not appear in the report.
 */
export function formatOcrTruncationNotice(
  result: Pick<OcrResult, 'total_pages' | 'pages_processed' | 'truncated'>,
): string | null {
  const { truncated, total_pages, pages_processed } = result
  if (!truncated || !total_pages || !pages_processed) return null
  if (pages_processed >= total_pages) return null

  const dropped = total_pages - pages_processed
  const pagesWereDropped = dropped === 1 ? 'page was' : 'pages were'
  return (
    `HEADS UP: this document has ${total_pages} pages but only the first ` +
    `${pages_processed} were read. ${dropped} ${pagesWereDropped} NOT analyzed — ` +
    `any clauses in the back (arbitration, fees, auto-renewal) won't show up below.`
  )
}
