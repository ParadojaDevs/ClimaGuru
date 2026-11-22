import { describe, it, expect } from 'vitest'
import { parseStamp, stampInfo, ageText, isStale } from './radarTime'

describe('radarTime', () => {
  describe('parseStamp', () => {
    it('returns null for invalid format', () => {
      expect(parseStamp('not-a-stamp')).toBeNull()
      expect(parseStamp('261115132')).toBeNull() // too short
      expect(parseStamp('26111513200')).toBeNull() // too long
      expect(parseStamp('')).toBeNull()
      expect(parseStamp(null)).toBeNull()
      expect(parseStamp(undefined)).toBeNull()
    })

    it('returns null for invalid date components', () => {
      expect(parseStamp('2613151320')).toBeNull() // month 13
      expect(parseStamp('2611321320')).toBeNull() // day 32
      expect(parseStamp('2611152420')).toBeNull() // hour 24
      expect(parseStamp('2611151360')).toBeNull() // minute 60
    })

    it('parses valid COT stamp to UTC milliseconds', () => {
      // 2611151320 = 2026-11-15 13:20 COT = 2026-11-15 18:20 UTC
      const utcMs = parseStamp('2611151320')
      expect(utcMs).not.toBeNull()
      const date = new Date(utcMs)
      expect(date.getUTCFullYear()).toBe(2026)
      expect(date.getUTCMonth()).toBe(10) // 0-indexed
      expect(date.getUTCDate()).toBe(15)
      expect(date.getUTCHours()).toBe(18) // 13 + 5 = 18 UTC
      expect(date.getUTCMinutes()).toBe(20)
    })

    it('round-trips correctly for various dates', () => {
      const testStamps = [
        '2601010000', // Jan 1, 2026 00:00 COT
        '2606151200', // Jun 15, 2026 12:00 COT
        '2612312359', // Dec 31, 2026 23:59 COT
      ]
      for (const stamp of testStamps) {
        const utcMs = parseStamp(stamp)
        expect(utcMs).not.toBeNull()
        // Verify round-trip
        const date = new Date(utcMs)
        const back = new Date(utcMs - 5 * 60 * 60 * 1000) // subtract COT offset
        expect(back.getUTCFullYear()).toBe(2000 + Number(stamp.slice(0, 2)))
        expect(back.getUTCMonth()).toBe(Number(stamp.slice(2, 4)) - 1)
        expect(back.getUTCDate()).toBe(Number(stamp.slice(4, 6)))
        expect(back.getUTCHours()).toBe(Number(stamp.slice(6, 8)))
        expect(back.getUTCMinutes()).toBe(Number(stamp.slice(8, 10)))
      }
    })
  })

  describe('stampInfo', () => {
    const NOW_MS = Date.UTC(2026, 10, 15, 18, 35, 0) // 2026-11-15 18:35 UTC = 13:35 COT

    it('returns null for invalid stamp', () => {
      expect(stampInfo('invalid', NOW_MS)).toBeNull()
    })

    it('returns label, age, and iso for valid stamp', () => {
      const info = stampInfo('2611151320', NOW_MS) // 13:20 COT, age ~15 min
      expect(info).not.toBeNull()
      expect(info.label).toBe('15/11 13:20 COT')
      expect(info.ageMin).toBe(15)
      expect(info.ageMinutes).toBe(15)
      expect(info.iso).toBe('2026-11-15T18:20:00.000Z')
      expect(info.stamp).toBe('2611151320')
    })

    it('calculates age correctly for older stamps', () => {
      const info = stampInfo('2611151200', NOW_MS) // 12:00 COT, age ~95 min
      expect(info.ageMin).toBe(95)
    })
  })

  describe('ageText', () => {
    it('returns empty string for invalid input', () => {
      expect(ageText(NaN)).toBe('')
      expect(ageText(Infinity)).toBe('')
      expect(ageText('invalid')).toBe('')
      expect(ageText(null)).toBe('')
    })

    it('returns "hace segundos" for age < 1 minute', () => {
      expect(ageText(0)).toBe('hace segundos')
      expect(ageText(0.5)).toBe('hace segundos')
    })

    it('returns "hace X min" for age < 90 minutes', () => {
      expect(ageText(1)).toBe('hace 1 min')
      expect(ageText(15)).toBe('hace 15 min')
      expect(ageText(89)).toBe('hace 89 min')
    })

    it('returns "hace X h" for age >= 90 minutes', () => {
      expect(ageText(90)).toBe('hace 2 h')
      expect(ageText(120)).toBe('hace 2 h')
      expect(ageText(180)).toBe('hace 3 h')
    })
  })

  describe('isStale', () => {
    it('returns false for non-numeric age', () => {
      expect(isStale('invalid', 60)).toBe(false)
      expect(isStale(NaN, 60)).toBe(false)
      expect(isStale(null, 60)).toBe(false)
    })

    it('returns false for non-numeric maxAgeMinutes', () => {
      expect(isStale(10, 'invalid')).toBe(false)
      expect(isStale(10, NaN)).toBe(false)
    })

    it('returns false when age <= maxAgeMinutes', () => {
      expect(isStale(10, 60)).toBe(false)
      expect(isStale(60, 60)).toBe(false)
    })

    it('returns true when age > maxAgeMinutes', () => {
      expect(isStale(61, 60)).toBe(true)
      expect(isStale(90, 60)).toBe(true)
    })
  })
})