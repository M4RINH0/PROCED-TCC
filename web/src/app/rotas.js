import { DomiciliosTela } from '../modules/arranjos/index.js'
import { EstruturaEtariaTela } from '../modules/estrutura-etaria/index.js'
import { PanoramaTela } from '../modules/projecoes/index.js'
import { SimuladorTela } from '../modules/simulador/index.js'

/* linhaDoTempo: a tela usa o ano da linha do tempo flutuante */
export const ROTAS = [
  { id: 'pan', titulo: 'Panorama', icone: 'pan', Tela: PanoramaTela, linhaDoTempo: true },
  { id: 'dom', titulo: 'Domicílios', icone: 'dom', Tela: DomiciliosTela, linhaDoTempo: true },
  { id: 'eta', titulo: 'Estrutura etária', icone: 'eta', Tela: EstruturaEtariaTela, linhaDoTempo: true },
  { id: 'sim', titulo: 'Simulador', icone: 'sim', Tela: SimuladorTela, linhaDoTempo: false },
]

export const ROTA_PADRAO = 'pan'

export function rotaDoHash(hash) {
  const id = (hash || '').replace(/^#/, '')
  return ROTAS.some((r) => r.id === id) ? id : ROTA_PADRAO
}
