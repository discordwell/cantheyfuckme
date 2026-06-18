import { defineConfig } from 'vitest/config'

// Unit tests cover pure logic (doc-type routing/normalization, affiliate
// selection, report formatting helpers), so the default node environment is
// enough — no jsdom or React renderer needed.
export default defineConfig({
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
})
