import { describe, it, expect } from 'vitest'
import {
  VISUALIZATION_EXACT,
  VISUALIZATION_APPROXIMATE,
  VISUALIZATION_BLOCKED,
  OVERLAY_MAX_AGE_MINUTES,
  DEFAULT_OVERLAY_OPACITY,
  clampOpacity,
  toLeafletBounds,
  overlayDecision,
} from './radarOverlayPolicy'

describe('radarOverlayPolicy', () => {
  describe('constants', () => {
    it('exports visualization policy constants', () => {
      expect(VISUALIZATION_EXACT).toBe('exact')
      expect(VISUALIZATION_APPROXIMATE).toBe('approximate_with_warning')
      expect(VISUALIZATION_BLOCKED).toBe('blocked')
    })

    it('exports freshness window and default opacity', () => {
      expect(OVERLAY_MAX_AGE_MINUTES).toBe(60)
      expect(DEFAULT_OVERLAY_OPACITY).toBe(0.65)
    })
  })

  describe('clampOpacity', () => {
    it('returns default for non-finite values', () => {
      expect(clampOpacity(NaN)).toBe(DEFAULT_OVERLAY_OPACITY)
      expect(clampOpacity(Infinity)).toBe(DEFAULT_OVERLAY_OPACITY)
      expect(clampOpacity(-Infinity)).toBe(DEFAULT_OVERLAY_OPACITY)
      expect(clampOpacity('invalid')).toBe(DEFAULT_OVERLAY_OPACITY)
      expect(clampOpacity(null)).toBe(DEFAULT_OVERLAY_OPACITY)
      expect(clampOpacity(undefined)).toBe(DEFAULT_OVERLAY_OPACITY)
    })

    it('clamps values to [0, 1]', () => {
      expect(clampOpacity(-0.5)).toBe(0)
      expect(clampOpacity(1.5)).toBe(1)
      expect(clampOpacity(0)).toBe(0)
      expect(clampOpacity(1)).toBe(1)
      expect(clampOpacity(0.3)).toBe(0.3)
    })
  })

  describe('toLeafletBounds', () => {
    it('returns null for invalid inputs', () => {
      expect(toLeafletBounds(null)).toBeNull()
      expect(toLeafletBounds(undefined)).toBeNull()
      expect(toLeafletBounds({})).toBeNull()
      expect(toLeafletBounds({ west: -70, south: 2 })).toBeNull()
    })

    it('returns null for non-finite coordinates', () => {
      expect(toLeafletBounds({ west: NaN, south: 2, east: -69, north: 3 })).toBeNull()
      expect(toLeafletBounds({ west: -70, south: Infinity, east: -69, north: 3 })).toBeNull()
    })

    it('returns null for inverted bounds', () => {
      expect(toLeafletBounds({ west: -69, south: 2, east: -70, north: 3 })).toBeNull()
      expect(toLeafletBounds({ west: -70, south: 3, east: -69, north: 2 })).toBeNull()
    })

    it('returns null for out-of-range coordinates', () => {
      expect(toLeafletBounds({ west: -181, south: 2, east: -69, north: 3 })).toBeNull()
      expect(toLeafletBounds({ west: -70, south: -91, east: -69, north: 3 })).toBeNull()
      expect(toLeafletBounds({ west: -70, south: 2, east: 181, north: 3 })).toBeNull()
      expect(toLeafletBounds({ west: -70, south: 2, east: -69, north: 91 })).toBeNull()
    })

    it('converts valid bounds to Leaflet format [[south, west], [north, east]]', () => {
      const result = toLeafletBounds({ west: -70, south: 2, east: -69, north: 3 })
      expect(result).toEqual([
        [2, -70],
        [3, -69],
      ])
    })
  })

  describe('overlayDecision', () => {
    const baseGeoref = {
      state: 'derived',
      visualization: VISUALIZATION_APPROXIMATE,
      render_allowed: true,
      warning: 'Posición aproximada: bounds derivados de GeoTIFF histórico, sin validación temporal con el PNG.',
    }

    it('blocks when georef is missing', () => {
      const decision = overlayDecision({ georef: null, ageMinutes: 10 })
      expect(decision.renderAllowed).toBe(false)
      expect(decision.reason).toBe('missing_georef')
    })

    it('blocks when render_allowed is false (BAR/CAR)', () => {
      const decision = overlayDecision({
        georef: { ...baseGeoref, render_allowed: false, state: 'assumed' },
        ageMinutes: 10,
      })
      expect(decision.renderAllowed).toBe(false)
      expect(decision.reason).toBe('blocked')
    })

    it('blocks when visualization is approximate but warning is missing', () => {
      const decision = overlayDecision({
        georef: { ...baseGeoref, warning: '' },
        ageMinutes: 10,
      })
      expect(decision.renderAllowed).toBe(false)
      expect(decision.reason).toBe('missing_warning')
    })

    it('blocks when frame is stale (exceeds max age)', () => {
      const decision = overlayDecision({
        georef: baseGeoref,
        ageMinutes: OVERLAY_MAX_AGE_MINUTES + 1,
      })
      expect(decision.renderAllowed).toBe(false)
      expect(decision.stale).toBe(true)
      expect(decision.reason).toBe('stale')
    })

    it('allows when all conditions are met', () => {
      const decision = overlayDecision({ georef: baseGeoref, ageMinutes: 10 })
      expect(decision.renderAllowed).toBe(true)
      expect(decision.approximate).toBe(true)
      expect(decision.warning).toBe(baseGeoref.warning)
      expect(decision.stale).toBe(false)
    })

    it('allows exact visualization without warning requirement', () => {
      const decision = overlayDecision({
        georef: {
          state: 'verified',
          visualization: VISUALIZATION_EXACT,
          render_allowed: true,
          warning: null,
        },
        ageMinutes: 10,
      })
      expect(decision.renderAllowed).toBe(true)
      expect(decision.approximate).toBe(false)
      expect(decision.warning).toBeNull()
    })

    it('treats non-numeric ageMinutes as not stale', () => {
      const decision = overlayDecision({ georef: baseGeoref, ageMinutes: 'invalid' })
      expect(decision.renderAllowed).toBe(true)
      expect(decision.stale).toBe(false)
    })

    it('uses custom maxAgeMinutes when provided', () => {
      const decision = overlayDecision({
        georef: baseGeoref,
        ageMinutes: 30,
        maxAgeMinutes: 20,
      })
      expect(decision.renderAllowed).toBe(false)
      expect(decision.stale).toBe(true)
    })
  })
})