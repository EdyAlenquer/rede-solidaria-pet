import 'leaflet/dist/leaflet.css'

import L from 'leaflet'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'
import type { ReactNode } from 'react'
import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet'

// Corrige o bug clássico dos ícones de marcador do Leaflet com bundlers:
// sem isto, o Leaflet tenta resolver os PNGs por caminho relativo e some.
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
})

export type PontoMapa = {
  id: number
  titulo: string
  latitude: number
  longitude: number
  /** Conteúdo opcional do popup (sobrepõe o título simples). */
  popup?: ReactNode
}

type MapaPedidosProps = {
  /** Pontos com coordenadas a marcar no mapa. */
  pontos?: PontoMapa[]
  /** Centro inicial [latitude, longitude]. Padrão: Brasil. */
  centro?: [number, number]
  /** Nível de zoom inicial. */
  zoom?: number
}

const CENTRO_BRASIL: [number, number] = [-14.235, -51.9253]

/**
 * Mapa Leaflet com marcadores de pedidos georreferenciados.
 *
 * Importa o CSS do Leaflet e corrige os ícones de marcador para funcionarem
 * com o bundler. Deve ser carregado apenas no navegador (o Leaflet acessa
 * `window`); rotas que o usam fazem import dinâmico para não quebrar testes.
 *
 * @param props - Pontos, centro e zoom iniciais.
 * @returns Container de mapa interativo.
 */
export function MapaPedidos({ pontos = [], centro = CENTRO_BRASIL, zoom = 4 }: MapaPedidosProps) {
  return (
    <MapContainer center={centro} zoom={zoom} className="rsp-mapa" scrollWheelZoom>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {pontos.map((ponto) => (
        <Marker key={ponto.id} position={[ponto.latitude, ponto.longitude]}>
          <Popup>{ponto.popup ?? ponto.titulo}</Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}

export default MapaPedidos
