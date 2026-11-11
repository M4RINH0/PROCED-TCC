import { render } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import Comparar from '../../src/pages/Comparar.jsx'
import Domicilios from '../../src/pages/Domicilios.jsx'
import EstruturaEtaria, { ARRANJOS } from '../../src/pages/EstruturaEtaria.jsx'
import Panorama from '../../src/pages/Panorama.jsx'
import Simulador from '../../src/pages/Simulador.jsx'
import {
  ARRANJOS_CONSUMO_CHEFE,
  CONSULTAS_AQUECIMENTO,
  CONSULTAS_INICIAIS,
  chaveDe,
  gerarDadosIniciais,
} from '../../src/services/dadosIniciais.js'
import { RECORTES } from '../../src/utils/series.js'

const CHAVES = new Set(CONSULTAS_INICIAIS.map(({ caminho, parametros }) => chaveDe(caminho, parametros)))
const pendente = () => vi.fn(() => new Promise(() => {}))
const resposta = (corpo) => ({ ok: true, json: () => Promise.resolve(corpo) })

describe('chaveDe', () => {
  it('ordena os parâmetros em ordem alfabética', () => {
    expect(chaveDe('/x', { recorte: 'a', k: 1, localidade: 'Brasil' })).toBe('/x?k=1&localidade=Brasil&recorte=a')
  })
  it('é a mesma em qualquer ordem de parâmetros', () => {
    expect(chaveDe('/x', { a: 1, b: 2 })).toBe(chaveDe('/x', { b: 2, a: 1 }))
  })
  it('ignora nulos e indefinidos, mas mantém o zero', () => {
    expect(chaveDe('/x', { a: null, b: undefined, c: 0 })).toBe('/x?c=0')
  })
  it('sem parâmetros devolve só o caminho', () => {
    expect(chaveDe('/fontes')).toBe('/fontes')
    expect(chaveDe('/fontes', {})).toBe('/fontes')
  })
  it('codifica a vírgula da lista de grupos', () => {
    expect(chaveDe('/comparacao', { grupos: 'uni_60,cas_60' })).toBe('/comparacao?grupos=uni_60%2Ccas_60')
  })
})

describe('CONSULTAS_INICIAIS', () => {
  it('não repete consulta', () => {
    expect(CHAVES.size).toBe(CONSULTAS_INICIAIS.length)
  })
  it('cobre todos os recortes do Panorama', () => {
    RECORTES.forEach((r) => expect([...CHAVES].some((c) => c.startsWith('/projecoes/serie?') && c.includes(`recorte=${r.id}`))).toBe(true))
  })
  it('cobre os mesmos arranjos do seletor da Estrutura etária', () => {
    expect(ARRANJOS_CONSUMO_CHEFE).toEqual(ARRANJOS.map((a) => a.id))
  })
  it('as consultas de aquecimento são consultas da abertura (nada fora do contrato)', () => {
    CONSULTAS_AQUECIMENTO.forEach(({ caminho, parametros }) => expect(CHAVES.has(chaveDe(caminho, parametros))).toBe(true))
  })
})

/* Se uma página mudar o padrão e a lista não acompanhar, o cache de abertura deixaria
   de valer em silêncio: estes testes conferem a primeira consulta de cada página. */
describe('cada página abre com uma consulta que está nos dados de abertura', () => {
  it('Panorama', () => {
    const buscar = pendente()
    render(<Panorama ano={2070} buscar={buscar} />)
    expect(CHAVES.has(chaveDe('/projecoes/serie', buscar.mock.calls[0][0]))).toBe(true)
  })
  it('Domicílios', () => {
    const buscar = pendente()
    render(<Domicilios ano={2070} buscar={buscar} />)
    expect(CHAVES.has(chaveDe('/arranjos/composicao', buscar.mock.calls[0][0]))).toBe(true)
  })
  it('Estrutura etária', () => {
    const buscarPir = pendente()
    const buscarConsumo = pendente()
    render(<EstruturaEtaria ano={2070} buscarPir={buscarPir} buscarConsumo={buscarConsumo} />)
    expect(CHAVES.has(chaveDe('/estrutura-etaria/piramides', buscarPir.mock.calls[0][0]))).toBe(true)
    expect(CHAVES.has(chaveDe('/estrutura-etaria/consumo-chefe', buscarConsumo.mock.calls[0][0]))).toBe(true)
  })
  it('Simulador', () => {
    const buscar = pendente()
    render(<Simulador buscar={buscar} />)
    expect(CHAVES.has(chaveDe('/simulador', buscar.mock.calls[0][0]))).toBe(true)
  })
  it('Comparar', () => {
    const buscar = pendente()
    render(<Comparar buscar={buscar} buscarSensInt={pendente()} buscarSensCob={pendente()} buscarSintReg={pendente()} />)
    const { grupos, ...resto } = buscar.mock.calls[0][0]
    expect(CHAVES.has(chaveDe('/comparacao', { grupos: grupos.join(','), ...resto }))).toBe(true)
  })
})

describe('gerarDadosIniciais', () => {
  const consultas = [
    { caminho: '/fontes', parametros: {} },
    { caminho: '/projecoes/serie', parametros: { recorte: 'a', k: 1 } },
  ]

  it('grava cada resposta pela chave, juntando o endereço da API sem barra dupla', async () => {
    const fetcher = vi.fn((url) => Promise.resolve(resposta({ url })))
    const { dados, falhas } = await gerarDadosIniciais('http://api/', { fetcher, consultas })
    expect(falhas).toEqual([])
    expect(dados).toEqual({
      '/fontes': { url: 'http://api/fontes' },
      '/projecoes/serie?k=1&recorte=a': { url: 'http://api/projecoes/serie?k=1&recorte=a' },
    })
  })

  it('consulta uma de cada vez, na ordem da lista', async () => {
    let abertas = 0
    let maximo = 0
    const ordem = []
    const fetcher = vi.fn(async (url) => {
      abertas += 1
      maximo = Math.max(maximo, abertas)
      ordem.push(url)
      await new Promise((r) => setTimeout(r, 5))
      abertas -= 1
      return resposta({})
    })
    await gerarDadosIniciais('http://api', { fetcher, consultas })
    expect(maximo).toBe(1)
    expect(ordem).toEqual(['http://api/fontes', 'http://api/projecoes/serie?k=1&recorte=a'])
  })

  it('deixa de fora a consulta com erro HTTP e segue com as outras', async () => {
    const fetcher = vi.fn((url) => Promise.resolve(url.endsWith('/fontes') ? { ok: false, status: 500 } : resposta({ ok: 1 })))
    const { dados, falhas } = await gerarDadosIniciais('http://api', { fetcher, consultas })
    expect(Object.keys(dados)).toEqual(['/projecoes/serie?k=1&recorte=a'])
    expect(falhas).toEqual(['/fontes (código 500)'])
  })

  it('com a API fora do ar, devolve nada e lista todas as falhas', async () => {
    const fetcher = vi.fn().mockRejectedValue(new TypeError('fetch failed'))
    const { dados, falhas } = await gerarDadosIniciais('http://api', { fetcher, consultas })
    expect(dados).toEqual({})
    expect(falhas).toHaveLength(2)
  })

  it('passa um sinal de tempo limite a cada consulta', async () => {
    const fetcher = vi.fn(() => Promise.resolve(resposta({})))
    await gerarDadosIniciais('http://api', { fetcher, consultas, tempoLimiteMs: 1000 })
    fetcher.mock.calls.forEach(([, opcoes]) => expect(opcoes.signal).toBeInstanceOf(AbortSignal))
  })
})
