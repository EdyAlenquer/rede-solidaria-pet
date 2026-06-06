import { render } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// O Leaflet acessa `window`/DOM ao montar e não roda bem em jsdom. Mocamos
// `react-leaflet` por componentes leves e capturamos `useMap` para inspecionar
// o comportamento de recentralização sem montar um mapa real.
const flyToMock = vi.fn()

vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TileLayer: () => null,
  Marker: () => <div data-testid="marcador" />,
  useMap: () => ({ flyTo: flyToMock }),
  useMapEvents: () => null,
}))

// Evita o efeito colateral de configurar ícones do Leaflet no import.
vi.mock('leaflet', () => ({
  default: { Icon: { Default: { mergeOptions: vi.fn() } } },
}))
vi.mock('leaflet/dist/leaflet.css', () => ({}))
vi.mock('leaflet/dist/images/marker-icon-2x.png', () => ({ default: 'a' }))
vi.mock('leaflet/dist/images/marker-icon.png', () => ({ default: 'b' }))
vi.mock('leaflet/dist/images/marker-shadow.png', () => ({ default: 'c' }))

import { MapaSelecao } from './MapaSelecao'

describe('MapaSelecao', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('recentraliza com flyTo quando o valor muda externamente', () => {
    const { rerender } = render(<MapaSelecao valor={null} onSelecionar={vi.fn()} />)
    expect(flyToMock).not.toHaveBeenCalled()

    rerender(
      <MapaSelecao valor={{ latitude: -23.5503, longitude: -46.6339 }} onSelecionar={vi.fn()} />,
    )

    expect(flyToMock).toHaveBeenCalledWith([-23.5503, -46.6339], 16)
  })
})
