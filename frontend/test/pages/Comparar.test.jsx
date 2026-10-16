import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import GraficoComparacao from '../../src/components/GraficoComparacao.jsx'
import Comparar, { EXPLICA_POR_PESSOA } from '../../src/pages/Comparar.jsx'
import { buscarComparacao, exportarComparacao } from '../../src/services/api.js'
import { FONTE_COMPARACAO } from '../../src/utils/fontes.js'

const ROTULOS = {
  uni_60: 'Unipessoal 60+',
  cas_60: 'Casal ou dupla 60+',
  mul_60: 'Multipessoal 60+',
  mono_60: 'Mononuclear 60+',
  todos_60: 'Todos 60+',
  mul_59: 'Multipessoal abaixo de 60',
}
/* Resposta no formato de /comparacao: índice crescente por grupo e tabela já calculada pela API */
const resposta = ({ grupos, indicador, forma, cenario, localidade }) => ({
  indicador,
  forma,
  cenario,
  unidade: 'domicílios',
  localidade,
  intensidade: 0.6,
  k: 1,
  simulacao: false,
  dados_ilustrativos: false,
  fonte: FONTE_COMPARACAO,
  grupos: grupos.map((id, i) => ({
    id,
    rotulo: ROTULOS[id],
    agregado: id.startsWith('mono') || id.startsWith('todos'),
    chefe_60_mais: id.endsWith('60'),
    arranjo: null,
    domicilios_amostra: 1000,
    baixa_confiabilidade: false,
    motivo_sem_valor: null,
    pontos: Array.from({ length: 45 }, (_, a) => ({ ano: 2026 + a, valor: 100 + a * (i + 1), valor_absoluto: 1000 + a, indice: 100 + a * (i + 1) })),
  })),
  tabela: grupos.map((id, i) => ({
    id,
    rotulo: ROTULOS[id],
    valor_2026: 5937636,
    valor_2050: 11904175,
    valor_2070: 14325336,
    variacao_absoluta: 8387700,
    variacao_pct: 141.3 + i * 10,
    ordem: grupos.length - i,
  })),
})
const buscarOk = () => vi.fn((p) => Promise.resolve(resposta(p)))

describe('api da comparação', () => {
  it('monta as URLs de /comparacao e /exportar/comparacao com os grupos separados por vírgula', async () => {
    const fetch = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}), blob: () => Promise.resolve(new Blob()), headers: { get: () => null } })
    vi.stubGlobal('fetch', fetch)
    const p = { grupos: ['uni_60', 'cas_60'], indicador: 'domicilios', forma: 'indice', cenario: 'taxas', localidade: 'DF', intensidade: 0.6, k: 1 }
    await buscarComparacao(p)
    await exportarComparacao({ ...p, formato: 'xlsx' })
    const [busca, baixa] = fetch.mock.calls.map((c) => new URL(c[0]))
    expect(busca.pathname).toBe('/comparacao')
    expect(busca.searchParams.get('grupos')).toBe('uni_60,cas_60')
    expect(baixa.pathname).toBe('/exportar/comparacao')
    expect(baixa.searchParams.get('formato')).toBe('xlsx')
    vi.unstubAllGlobals()
  })
})

describe('Comparar', () => {
  it('abre com o atalho "Arranjos com chefe 60+", índice e o cenário envelhecimento e arranjos', async () => {
    const buscar = buscarOk()
    render(<Comparar buscar={buscar} />)
    await screen.findByTestId('tabela-comparacao')
    expect(buscar.mock.calls[0][0]).toMatchObject({ grupos: ['uni_60', 'cas_60', 'mul_60'], indicador: 'domicilios', forma: 'indice', cenario: 'taxas', localidade: 'Brasil' })
    expect(screen.getByLabelText('Cenário')).toHaveValue('taxas')
    expect(screen.getByRole('option', { name: 'Envelhecimento e arranjos' })).toBeInTheDocument()
  })

  it('mostra a frase-resumo com quem cresce mais e quem cresce menos', async () => {
    render(<Comparar buscar={buscarOk()} />)
    await waitFor(() => expect(screen.getByTestId('frase-comparacao')).toHaveTextContent('cresce'))
    expect(screen.getByTestId('frase-comparacao')).toHaveTextContent(
      'De 2026 a 2070, no cenário envelhecimento e arranjos, o grupo multipessoal 60+ cresce 161,3%, contra 141,3% do grupo unipessoal 60+.',
    )
  })

  it('tabela com 2026, 2050, 2070, variações e ordem em formato brasileiro', async () => {
    render(<Comparar buscar={buscarOk()} />)
    const tabela = await screen.findByTestId('tabela-comparacao')
    const linha = within(tabela).getByText('Unipessoal 60+').closest('tr')
    expect(within(linha).getAllByRole('cell').map((c) => c.textContent)).toEqual([
      'Unipessoal 60+',
      '5.937.636',
      '11.904.175',
      '14.325.336',
      '+8.387.700',
      '+141,3%',
      '3º',
    ])
  })

  it('o consumo por pessoa só fica disponível com agregados, e a página explica por quê', async () => {
    render(<Comparar buscar={buscarOk()} />)
    await screen.findByTestId('tabela-comparacao')
    expect(screen.getByRole('option', { name: 'Consumo por pessoa (só agregados)' })).toBeDisabled()
    expect(screen.getByTestId('explica-por-pessoa')).toHaveTextContent(EXPLICA_POR_PESSOA)
    fireEvent.click(screen.getByRole('button', { name: 'Mononucleares: 60+ contra abaixo de 60' }))
    expect(screen.getByRole('option', { name: 'Consumo por pessoa (só agregados)' })).toBeEnabled()
    expect(screen.queryByTestId('explica-por-pessoa')).not.toBeInTheDocument()
  })

  it('escolher uma célula com consumo por pessoa volta o indicador para domicílios e avisa', async () => {
    const avisar = vi.fn()
    render(<Comparar buscar={buscarOk()} avisar={avisar} />)
    await screen.findByTestId('tabela-comparacao')
    fireEvent.click(screen.getByRole('button', { name: 'Todos: 60+ contra abaixo de 60' }))
    fireEvent.change(screen.getByLabelText('Indicador'), { target: { value: 'consumo_por_pessoa' } })
    fireEvent.click(screen.getByRole('button', { name: /^Unipessoal 60\+$/ }))
    expect(screen.getByLabelText('Indicador')).toHaveValue('domicilios')
    expect(avisar).toHaveBeenCalledWith(expect.stringContaining('só vale para agregados'))
  })

  it('mantém de 2 a 6 grupos', async () => {
    const avisar = vi.fn()
    render(<Comparar buscar={buscarOk()} avisar={avisar} />)
    await screen.findByTestId('tabela-comparacao')
    fireEvent.click(screen.getByRole('button', { name: '60+ contra abaixo de 60 no multipessoal' }))
    fireEvent.click(screen.getByRole('button', { name: /^Multipessoal 60\+$/ }))
    expect(avisar).toHaveBeenCalledWith('Mantenha ao menos 2 grupos')
    for (const nome of ['Unipessoal 60+', 'Casal ou dupla 60+', 'Unipessoal abaixo de 60', 'Casal ou dupla abaixo de 60']) {
      fireEvent.click(screen.getByRole('button', { name: new RegExp(`^${nome.replace('+', '\\+')}$`) }))
    }
    fireEvent.click(screen.getByRole('button', { name: /^Todos 60\+$/ }))
    expect(avisar).toHaveBeenCalledWith('Escolha no máximo 6 grupos')
    expect(screen.getByRole('button', { name: /^Todos 60\+$/ })).toHaveAttribute('aria-pressed', 'false')
  })

  it('envia forma, cenário, localidade e os controles de simulação aplicados', async () => {
    const buscar = buscarOk()
    const simulacao = { valores: { k: 1.3, intensidade: 1 }, aplicados: { k: 1.3, intensidade: 1 }, ativa: true, aoMudar: vi.fn(), restaurar: vi.fn() }
    render(<Comparar buscar={buscar} simulacao={simulacao} local={{ valor: 'DF', nome: 'Distrito Federal', regioes: [], aoMudar: () => {} }} />)
    await screen.findByTestId('tabela-comparacao')
    fireEvent.click(screen.getByRole('button', { name: 'Valores absolutos' }))
    fireEvent.change(screen.getByLabelText('Cenário'), { target: { value: 'contrafactual' } })
    await waitFor(() => expect(buscar).toHaveBeenLastCalledWith(expect.objectContaining({ forma: 'absoluto', cenario: 'contrafactual', localidade: 'DF', k: 1.3, intensidade: 1 }), expect.anything()))
  })

  it('no erro, mostra o estado no contexto e cita as mesmas fontes do estado normal', async () => {
    render(<Comparar buscar={vi.fn().mockRejectedValue(new Error('A API respondeu com o código 503'))} />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Unipessoal 60+, Casal ou dupla 60+, Multipessoal 60+, Brasil')
    expect(screen.getByText(`Fonte: ${FONTE_COMPARACAO}`, { exact: false })).toBeInTheDocument()
  })

  it('lista o motivo dos grupos sem valor', async () => {
    const buscar = vi.fn((p) => {
      const r = resposta(p)
      r.grupos[0].motivo_sem_valor = 'Falta amostra da POF em alguma faixa do grupo nesta localidade.'
      return Promise.resolve(r)
    })
    render(<Comparar buscar={buscar} />)
    expect(await screen.findByTestId('motivos-sem-valor')).toHaveTextContent('Unipessoal 60+: Falta amostra da POF')
  })

  it('exporta a comparação com os parâmetros da tela', async () => {
    const exportar = vi.fn().mockResolvedValue({ blob: new Blob(['x']), nomeArquivo: 'proced_comparacao_Brasil_2026_2070.csv' })
    const avisar = vi.fn()
    render(<Comparar buscar={buscarOk()} exportar={exportar} avisar={avisar} />)
    await screen.findByTestId('tabela-comparacao')
    fireEvent.click(screen.getByRole('button', { name: 'CSV' }))
    await waitFor(() => expect(avisar).toHaveBeenCalledWith('Comparação exportada em CSV'))
    expect(exportar).toHaveBeenCalledWith(expect.objectContaining({ formato: 'csv', grupos: ['uni_60', 'cas_60', 'mul_60'], forma: 'indice' }))
  })
})

describe('GraficoComparacao', () => {
  const grupos = resposta({ grupos: ['uni_60', 'mul_59', 'todos_60'], indicador: 'domicilios', forma: 'indice', cenario: 'taxas', localidade: 'Brasil' }).grupos

  it('uma linha por grupo, com o estilo do grupo, rótulo direto e a linha de base 100 no índice', () => {
    render(<GraficoComparacao grupos={grupos} forma="indice" unidade="domicílios" />)
    expect(screen.getByTestId('linha-cmp-uni_60')).toHaveAttribute('stroke', 'var(--g-unipessoal)')
    expect(screen.getByTestId('linha-cmp-mul_59')).toHaveAttribute('stroke-dasharray', '7 5')
    expect(screen.getByTestId('linha-cmp-todos_60')).toHaveAttribute('stroke', 'var(--g-agregado)')
    expect(screen.getByTestId('rotulo-cmp-uni_60')).toHaveTextContent('Unipessoal 60+144 em 2070')
    expect(screen.getByTestId('base-100')).toBeInTheDocument()
  })

  it('valores absolutos sem linha de base e grupo sem valor sem linha', () => {
    const semValor = { ...grupos[0], id: 'mul_60', rotulo: 'Multipessoal 60+', pontos: grupos[0].pontos.map((p) => ({ ...p, valor: null })) }
    render(<GraficoComparacao grupos={[grupos[1], semValor]} forma="absoluto" unidade="domicílios" />)
    expect(screen.queryByTestId('base-100')).not.toBeInTheDocument()
    expect(screen.queryByTestId('linha-cmp-mul_60')).not.toBeInTheDocument()
  })
})
