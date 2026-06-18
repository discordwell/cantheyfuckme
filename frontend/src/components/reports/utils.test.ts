import { describe, it, expect } from 'vitest'
import { getStatusColor, getStatusLabel, getRiskColor, getRiskLabel } from './utils'

describe('getStatusColor', () => {
  it('maps pass/warning/fail families and defaults to gray', () => {
    expect(getStatusColor('pass')).toBe('var(--pixel-green)')
    expect(getStatusColor('compliant')).toBe('var(--pixel-green)')
    expect(getStatusColor('warning')).toBe('var(--pixel-yellow)')
    expect(getStatusColor('fail')).toBe('var(--pixel-red)')
    expect(getStatusColor('non-compliant')).toBe('var(--pixel-red)')
    expect(getStatusColor('whatever')).toBe('var(--pixel-gray)')
  })
})

describe('getStatusLabel', () => {
  it('formats known statuses and uppercases the rest', () => {
    expect(getStatusLabel('compliant')).toBe('COMPLIANT')
    expect(getStatusLabel('non-compliant')).toBe('NON-COMPLIANT')
    expect(getStatusLabel('needs-review')).toBe('NEEDS REVIEW')
    expect(getStatusLabel('pass')).toBe('PASS')
  })
})

describe('getRiskColor', () => {
  it('covers the 5-tier severity hierarchy and defaults to gray', () => {
    expect(getRiskColor('dealbreaker')).toBe('#d32f2f')
    expect(getRiskColor('high')).toBe('var(--pixel-red)')
    expect(getRiskColor('critical')).toBe('var(--pixel-red)')
    expect(getRiskColor('medium')).toBe('var(--pixel-yellow)')
    expect(getRiskColor('minor')).toBe('#78909c')
    expect(getRiskColor('low')).toBe('var(--pixel-green)')
    expect(getRiskColor('boilerplate')).toBe('var(--pixel-green)')
    expect(getRiskColor('mystery')).toBe('var(--pixel-gray)')
  })
})

describe('getRiskLabel', () => {
  it('formats known risks and uppercases unknown ones', () => {
    expect(getRiskLabel('dealbreaker')).toBe('DEALBREAKER')
    expect(getRiskLabel('high')).toBe('HIGH RISK')
    expect(getRiskLabel('medium')).toBe('MEDIUM RISK')
    expect(getRiskLabel('low')).toBe('LOW RISK')
    expect(getRiskLabel('minor')).toBe('MINOR')
    expect(getRiskLabel('boilerplate')).toBe('STANDARD')
    expect(getRiskLabel('info')).toBe('INFO')
  })
})
