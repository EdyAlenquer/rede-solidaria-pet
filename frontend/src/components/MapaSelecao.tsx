import 'leaflet/dist/leaflet.css'

import L from 'leaflet'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'
import { useEffect } from 'react'
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from 'react-leaflet'

// Corrige o bug clássico dos ícones de marcador do Leaflet com bundlers:
// sem isto, o Leaflet tenta resolver os PNGs por caminho relativo e some.
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
})

export type Coordenada = {
  latitude: number
  longitude: number
}

type MapaSelecaoProps = {
  /** Ponto atualmente selecionado, ou `null` quando nenhum. */
  valor: Coordenada | null
  /** Chamado quando o usuário clica no mapa para escolher um ponto. */
  onSelecionar: (coordenada: Coordenada) => void
  /** Centro inicial [latitude, longitude]. Padrão: Brasil. */
  centro?: [number, number]
  /** Nível de zoom inicial. */
  zoom?: number
}

const CENTRO_BRASIL: [number, number] = [-14.235, -51.9253]

type SeletorPontoProps = {
  onSelecionar: (coordenada: Coordenada) => void
}

/**
 * Captura cliques no mapa e reporta a coordenada escolhida.
 *
 * Componente interno sem renderização visível; usa `useMapEvents` para
 * escutar o clique do usuário.
 *
 * @param props - Callback de seleção de ponto.
 * @returns `null` (apenas registra o handler de eventos).
 */
function SeletorPonto({ onSelecionar }: SeletorPontoProps) {
  useMapEvents({
    click(evento) {
      onSelecionar({ latitude: evento.latlng.lat, longitude: evento.latlng.lng })
    },
  })
  return null
}

/** Nível de zoom usado ao recentralizar o mapa num endereço escolhido. */
const ZOOM_ENDERECO = 16

type RecentralizarMapaProps = {
  /** Ponto a seguir; quando muda, o mapa voa até ele. */
  valor: Coordenada | null
}

/**
 * Recentraliza o mapa quando o ponto selecionado muda externamente.
 *
 * Componente interno sem renderização visível. Usa `useMap` para acessar a
 * instância do Leaflet e chama `flyTo` sempre que `valor` muda (por exemplo,
 * ao escolher um endereço na busca por texto), de modo que o mapa siga o ponto
 * recém-fixado. O clique-para-marcar continua disponível via `SeletorPonto`.
 *
 * @param props - Ponto atual a ser seguido.
 * @returns `null` (apenas dispara o efeito de recentralização).
 */
function RecentralizarMapa({ valor }: RecentralizarMapaProps) {
  const map = useMap()
  useEffect(() => {
    if (valor) {
      map.flyTo([valor.latitude, valor.longitude], ZOOM_ENDERECO)
    }
  }, [map, valor])
  return null
}

/**
 * Mapa Leaflet para selecionar um ponto (latitude/longitude).
 *
 * Clicar no mapa define o ponto e exibe um marcador. Quando o `valor` muda por
 * fora (ex.: busca de endereço por texto), o mapa voa até o novo ponto via
 * `RecentralizarMapa`. Importa o CSS do Leaflet e corrige os ícones de marcador
 * para o bundler. O Leaflet acessa `window` ao carregar; rotas que o usam devem
 * fazer import dinâmico para não quebrar os testes (que mocam `react-leaflet`).
 *
 * @param props - Ponto selecionado, callback de seleção, centro e zoom.
 * @returns Container de mapa interativo com seleção de ponto.
 */
export function MapaSelecao({
  valor,
  onSelecionar,
  centro = CENTRO_BRASIL,
  zoom = 4,
}: MapaSelecaoProps) {
  const centroInicial: [number, number] = valor
    ? [valor.latitude, valor.longitude]
    : centro
  return (
    <MapContainer
      center={centroInicial}
      zoom={valor ? 13 : zoom}
      className="rsp-mapa rsp-mapa--selecao"
      scrollWheelZoom
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <SeletorPonto onSelecionar={onSelecionar} />
      <RecentralizarMapa valor={valor} />
      {valor && <Marker position={[valor.latitude, valor.longitude]} />}
    </MapContainer>
  )
}

export default MapaSelecao
