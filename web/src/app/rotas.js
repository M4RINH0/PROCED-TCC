import { DomiciliosTela } from '../modules/arranjos/index.js'
import { EstruturaEtariaTela } from '../modules/estrutura-etaria/index.js'
import { PanoramaTela } from '../modules/projecoes/index.js'
import { SimuladorTela } from '../modules/simulador/index.js'

export const ROTAS = [
  { id: 'pan', titulo: 'Panorama', Tela: PanoramaTela },
  { id: 'dom', titulo: 'Domicílios', Tela: DomiciliosTela },
  { id: 'eta', titulo: 'Estrutura etária', Tela: EstruturaEtariaTela },
  { id: 'sim', titulo: 'Simulador', Tela: SimuladorTela },
]

export const ROTA_PADRAO = 'pan'

export function rotaDoHash(hash) {
  const id = (hash || '').replace(/^#/, '')
  return ROTAS.some((r) => r.id === id) ? id : ROTA_PADRAO
}
