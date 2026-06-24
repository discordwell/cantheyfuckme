// Shape of the /api/ocr response. The page fields are present for real
// extractions (PDF + image); the mock-mode placeholder omits them, so they are
// optional and consumers must treat their absence as "no page information".
export interface OcrResult {
  text: string
  total_pages?: number
  pages_processed?: number
  truncated?: boolean
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
