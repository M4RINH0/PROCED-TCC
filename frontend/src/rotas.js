import Comparar from './pages/Comparar.jsx'
import Domicilios from './pages/Domicilios.jsx'
import EstruturaEtaria from './pages/EstruturaEtaria.jsx'
import Panorama from './pages/Panorama.jsx'
import Simulador from './pages/Simulador.jsx'

/* linhaDoTempo: a tela usa o ano da linha do tempo flutuante */
export const ROTAS = [
  { id: 'pan', titulo: 'Panorama', icone: 'pan', Tela: Panorama, linhaDoTempo: true },
  { id: 'dom', titulo: 'Domicílios', icone: 'dom', Tela: Domicilios, linhaDoTempo: true },
  { id: 'eta', titulo: 'Estrutura etária', icone: 'eta', Tela: EstruturaEtaria, linhaDoTempo: true },
  { id: 'sim', titulo: 'Simulador', icone: 'sim', Tela: Simulador, linhaDoTempo: false },
  { id: 'cmp', titulo: 'Comparar', icone: 'cmp', Tela: Comparar, linhaDoTempo: false },
]

export const ROTA_PADRAO = 'pan'

export function rotaDoHash(hash) {
  const id = (hash || '').replace(/^#/, '')
  return ROTAS.some((r) => r.id === id) ? id : ROTA_PADRAO
}
