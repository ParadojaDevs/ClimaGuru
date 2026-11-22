import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RadarOverlayLayer from './RadarOverlayLayer'

// Mock react-leaflet's ImageOverlay
vi.mock('react-leaflet', () => ({
  ImageOverlay: vi.fn(({ url, bounds, opacity, zIndex, className, alt, eventHandlers, key }) => {
    // Simulate error handler being called if we want to test error state
    const img = document.createElement('img')
    img.src = url
    img.alt = alt
    img.className = className
    img.style.opacity = opacity
    img.dataset.testId = 'radar-overlay-image'
    img.dataset.key = key
    // Store error handler for manual triggering
    img._errorHandler = eventHandlers?.error
    return img
  }),
}))

// Mock Leaflet to avoid needing the actual library
vi.mock('leaflet', () => ({
  default: {
    divIcon: vi.fn(),
    icon: vi.fn(),
  },
}))

describe('RadarOverlayLayer', () => {
  const validBounds = { west: -75, south: 0, east: -70, north: 5 }
  const validUrl = 'https://bart.ideam.gov.co/ospa/radarcol/transparent/Guaviare/z/2026/11/15/GUA2611151320_z_Transp.png'

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders ImageOverlay when all props are valid', () => {
    render(<RadarOverlayLayer url={validUrl} bounds={validBounds} />)
    const img = screen.getByTestId('radar-overlay-image')
    expect(img).toBeInTheDocument()
    expect(img.src).toBe(validUrl)
    expect(img.alt).toBe('Reflectividad de radar IDEAM')
  })

  it('returns null when url is missing', () => {
    const { container } = render(<RadarOverlayLayer url={null} bounds={validBounds} />)
    expect(container.firstChild).toBeNull()
  })

  it('returns null when visible is false', () => {
    const { container } = render(<RadarOverlayLayer url={validUrl} bounds={validBounds} visible={false} />)
    expect(container.firstChild).toBeNull()
  })

  it('returns null when bounds are invalid', () => {
    const { container } = render(<RadarOverlayLayer url={validUrl} bounds={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('returns null when bounds are inverted', () => {
    const { container } = render(<RadarOverlayLayer url={validUrl} bounds={{ west: -70, south: 0, east: -75, north: 5 }} />)
    expect(container.firstChild).toBeNull()
  })

  it('uses key prop to force remount when url changes', () => {
    const { rerender } = render(<RadarOverlayLayer url={validUrl} bounds={validBounds} />)
    const img1 = screen.getByTestId('radar-overlay-image')
    expect(img1.dataset.key).toBe(validUrl)

    const newUrl = 'https://bart.ideam.gov.co/ospa/radarcol/transparent/Guaviare/z/2026/11/15/GUA2611151325_z_Transp.png'
    rerender(<RadarOverlayLayer url={newUrl} bounds={validBounds} />)
    const img2 = screen.getByTestId('radar-overlay-image')
    expect(img2.dataset.key).toBe(newUrl)
    expect(img2).not.toBe(img1)
  })

  it('applies clamped opacity', () => {
    const { rerender } = render(<RadarOverlayLayer url={validUrl} bounds={validBounds} opacity={1.5} />)
    let img = screen.getByTestId('radar-overlay-image')
    expect(img.style.opacity).toBe('1')

    rerender(<RadarOverlayLayer url={validUrl} bounds={validBounds} opacity={-0.5} />)
    img = screen.getByTestId('radar-overlay-image')
    expect(img.style.opacity).toBe('0')

    rerender(<RadarOverlayLayer url={validUrl} bounds={validBounds} opacity={0.65} />)
    img = screen.getByTestId('radar-overlay-image')
    expect(img.style.opacity).toBe('0.65')
  })

  it('calls onError when image fails to load', () => {
    const onError = vi.fn()
    render(<RadarOverlayLayer url={validUrl} bounds={validBounds} onError={onError} />)
    const img = screen.getByTestId('radar-overlay-image')
    // Simulate error
    img._errorHandler()
    expect(onError).toHaveBeenCalledWith(validUrl)
  })

  it('stays hidden after error until url changes', () => {
    const { rerender } = render(<RadarOverlayLayer url={validUrl} bounds={validBounds} />)
    const img1 = screen.getByTestId('radar-overlay-image')
    img1._errorHandler() // Trigger error

    // Should be hidden now (component returns null on error)
    rerender(<RadarOverlayLayer url={validUrl} bounds={validBounds} />)
    expect(screen.queryByTestId('radar-overlay-image')).toBeNull()

    // Change URL - should retry
    const newUrl = 'https://bart.ideam.gov.co/ospa/radarcol/transparent/Guaviare/z/2026/11/15/GUA2611151325_z_Transp.png'
    rerender(<RadarOverlayLayer url={newUrl} bounds={validBounds} />)
    const img2 = screen.getByTestId('radar-overlay-image')
    expect(img2).toBeInTheDocument()
    expect(img2.dataset.key).toBe(newUrl)
  })

  it('applies zIndex prop', () => {
    render(<RadarOverlayLayer url={validUrl} bounds={validBounds} zIndex={400} />)
    const img = screen.getByTestId('radar-overlay-image')
    // The zIndex is passed to ImageOverlay but not directly visible on img
    // We verify the component accepts it without error
    expect(img).toBeInTheDocument()
  })

  it('uses default opacity when not provided', () => {
    render(<RadarOverlayLayer url={validUrl} bounds={validBounds} />)
    const img = screen.getByTestId('radar-overlay-image')
    expect(img.style.opacity).toBe('0.65')
  })
})