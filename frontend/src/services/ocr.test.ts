import { describe, it, expect } from 'vitest'
import { formatOcrError, formatOcrTruncationNotice, OCR_BACKEND_DOWN_MESSAGE } from './ocr'

describe('formatOcrError', () => {
  it("surfaces the backend's actionable detail for a rejected upload", () => {
    // The upload hook re-throws a 4xx `detail` as an Error; the user needs to
    // see it (e.g. remove the PDF password) rather than a generic line.
    const err = new Error('That PDF is password-protected. Remove the password and upload it again.')
    expect(formatOcrError(err)).toBe(err.message)
  })

  it('points at the backend when fetch failed with a TypeError (never reached the server)', () => {
    // fetch rejects with a TypeError on a network failure; its message
    // ("Failed to fetch") is not something the user can act on.
    expect(formatOcrError(new TypeError('Failed to fetch'))).toBe(OCR_BACKEND_DOWN_MESSAGE)
  })

  it('falls back to the backend message for an Error with no message', () => {
    expect(formatOcrError(new Error(''))).toBe(OCR_BACKEND_DOWN_MESSAGE)
  })

  it('falls back to the backend message for a non-Error throw', () => {
    expect(formatOcrError('boom')).toBe(OCR_BACKEND_DOWN_MESSAGE)
    expect(formatOcrError(undefined)).toBe(OCR_BACKEND_DOWN_MESSAGE)
  })
})

describe('formatOcrTruncationNotice', () => {
  it('returns a notice naming both page counts when a PDF was truncated', () => {
    const notice = formatOcrTruncationNotice({
      truncated: true,
      total_pages: 12,
      pages_processed: 5,
    })
    expect(notice).not.toBeNull()
    expect(notice).toContain('12 pages')
    expect(notice).toContain('first 5')
    expect(notice).toContain('7 pages were NOT analyzed')
  })

  it('uses grammatical singular when exactly one page was dropped', () => {
    const notice = formatOcrTruncationNotice({
      truncated: true,
      total_pages: 6,
      pages_processed: 5,
    })
    expect(notice).toContain('1 page was NOT analyzed')
    expect(notice).not.toContain('1 pages were NOT analyzed')
  })

  it('returns null when nothing was truncated', () => {
    expect(
      formatOcrTruncationNotice({ truncated: false, total_pages: 3, pages_processed: 3 }),
    ).toBeNull()
  })

  it('returns null when page counts are missing (e.g. mock mode or an image)', () => {
    expect(formatOcrTruncationNotice({})).toBeNull()
    expect(formatOcrTruncationNotice({ truncated: true })).toBeNull()
  })

  it('returns null defensively if pages_processed is not actually fewer than total', () => {
    // Guards against a malformed response where truncated is set but the counts
    // do not agree; we should not invent a scary, nonsensical warning.
    expect(
      formatOcrTruncationNotice({ truncated: true, total_pages: 5, pages_processed: 5 }),
    ).toBeNull()
  })
})
