import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import RadarOverlayLayer from './RadarOverlayLayer'

// Mock react-leaflet's ImageOverlay with a proper React component factory
vi.mock('react-leaflet', () => {
  const errorHandlers = new Map()

  const MockImageOverlay = ({ url, bounds, opacity, zIndex, className, alt, eventHandlers, ...props }) => {
    // Use a custom prop for testing since React's key is not passed to components
    const testKey = props['data-test-key'] || url
    errorHandlers.set(testKey, eventHandlers?.error)
    return (
      <img
        data-testid="radar-overlay-image"
        data-test-key={testKey}
        src={url}
        alt={alt}
        className={className}
        style={{ opacity }}
      />
    )
  }

  MockImageOverlay.triggerError = (key) => {
    const handler = errorHandlers.get(key)
    if (handler) handler()
  }

  return { ImageOverlay: MockImageOverlay }
})

vi.mock('leaflet', () => ({
  default: {
    divIcon: vi.fn(),
    icon: vi.fn(),
  },
}))

describe('RadarOverlayLayer', () => {
  const validBounds = { west: -75, south: 0, east: -70, north: 5 }
  const validUrl = 'https://bart.ideam.gov.co/ospa/radarcol/transparent/Guaviare/z/2026/11/15/GUA2611151320_z_Transp.png'

  let MockImageOverlay

  beforeEach(async () => {
    vi.clearAllMocks()
    const { ImageOverlay } = await vi.importMock('react-leaflet')
    MockImageOverlay = ImageOverlay
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

  it('remounts when url changes (key prop behavior)', () => {
    const { rerender } = render(<RadarOverlayLayer url={validUrl} bounds={validBounds} />)
    const img1 = screen.getByTestId('radar-overlay-image')
    expect(img1.dataset.testKey).toBe(validUrl)

    const newUrl = 'https://bart.ideam.gov.co/ospa/radarcol/transparent/Guaviare/z/2026/11/15/GUA2611151325_z_Transp.png'
    rerender(<RadarOverlayLayer url={newUrl} bounds={validBounds} />)
    const img2 = screen.getByTestId('radar-overlay-image')
    expect(img2.dataset.testKey).toBe(newUrl)
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
    MockImageOverlay.triggerError(img.dataset.testKey)
    expect(onError).toHaveBeenCalledWith(validUrl)
  })

  it('stays hidden after error until url changes', () => {
    const { rerender } = render(<RadarOverlayLayer url={validUrl} bounds={validBounds} />)
    const img1 = screen.getByTestId('radar-overlay-image')
    MockImageOverlay.triggerError(img1.dataset.testKey)

    rerender(<RadarOverlayLayer url={validUrl} bounds={validBounds} />)
    expect(screen.queryByTestId('radar-overlay-image')).toBeNull()

    const newUrl = 'https://bart.ideam.gov.co/ospa/radarcol/transparent/Guaviare/z/2026/11/15/GUA2611151325_z_Transp.png'
    rerender(<RadarOverlayLayer url={newUrl} bounds={validBounds} />)
    const img2 = screen.getByTestId('radar-overlay-image')
    expect(img2).toBeInTheDocument()
    expect(img2.dataset.testKey).toBe(newUrl)
  })

  it('applies zIndex prop', () => {
    render(<RadarOverlayLayer url={validUrl} bounds={validBounds} zIndex={400} />)
    const img = screen.getByTestId('radar-overlay-image')
    expect(img).toBeInTheDocument()
  })

  it('uses default opacity when not provided', () => {
    render(<RadarOverlayLayer url={validUrl} bounds={validBounds} />)
    const img = screen.getByTestId('radar-overlay-image')
    expect(img.style.opacity).toBe('0.65')
  })

  it('se limpia al desmontar el mapa', () => {
    const { unmount } = render(
      <RadarOverlayLayer url={validUrl} bounds={validBounds} />
    )
    expect(screen.getByTestId('radar-overlay-image')).toBeInTheDocument()

    unmount()
    expect(screen.queryByTestId('radar-overlay-image')).toBeNull()
  })
})