import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { buscarArranjos, buscarComposicao } from '../../src/services/api.js'
import { noFiltro } from '../../src/utils/categorias.js'
import Domicilios from '../../src/pages/Domicilios.jsx'

const cat = (id, arranjo, idoso, casas, pct, kwh) => ({
  id,
  arranjo,
  chefe_60_mais: idoso,
  mononuclear: arranjo !== 'Multipessoal (3+)',
  domicilios_amostra: 1000,
  consumo_per_capita_kwh: kwh,
  participacao_pct: pct,
  casas,
})
const composicao = {
  anos: [2026, 2070],
  fonte: 'POF 2017 a 2018 e Projeções da População (IBGE)',
  categorias: [
    cat('uni_60', 'Unipessoal (Mononuclear)', true, [8, 14], [8.4, 14.2], 115.7),
    cat('cas_60', 'Casal ou Dupla', true, [13, 21], [12.9, 20.8], 81.4),
    cat('uni_59', 'Unipessoal (Mononuclear)', false, [6, 4], [6.0, 4.1], 114.8),
    cat('cas_59', 'Casal ou Dupla', false, [14, 10], [14.0, 10.1], 77.1),
    cat('mul_60', 'Multipessoal (3+)', true, [14, 22], [14.1, 21.9], 55.0),
    cat('mul_59', 'Multipessoal (3+)', false, [45, 29], [44.6, 28.9], null),
  ],
}
const buscar = () => vi.fn(() => Promise.resolve(composicao))

describe('api de arranjos', () => {
  it('monta as URLs', async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) })
    await buscarArranjos({ grupo: 'abaixo_60' }, { fetcher, base: 'http://api' })
    await buscarComposicao({ localidade: 'DF' }, { fetcher, base: 'http://api' })
    expect(fetcher.mock.calls.map((c) => c[0])).toEqual(['http://api/arranjos?grupo=abaixo_60', 'http://api/arranjos/composicao?localidade=DF'])
  })
})

describe('noFiltro', () => {
  it('separa recorte e mononucleares', () => {
    const [uni60, , uni59, , mul60] = composicao.categorias
    expect([noFiltro(uni60, 'rec'), noFiltro(uni59, 'rec'), noFiltro(uni59, 'mono'), noFiltro(mul60, 'mono')]).toEqual([true, false, true, false])
    expect(noFiltro(mul60, 'todos')).toBe(true)
  })
})

describe('Domicilios', () => {
  it('desenha 100 casas e descreve o recorte no ano', async () => {
    const { container } = render(<Domicilios ano={2070} buscar={buscar()} />)
    expect(await screen.findByText('35 de cada 100 domicílios')).toBeInTheDocument()
    expect(screen.getByText(/Em 2026 eram 21/)).toBeInTheDocument()
    expect(container.querySelectorAll('path.hs')).toHaveLength(100)
    expect(container.querySelectorAll('path.hs.h-u60')).toHaveLength(14)
  })

  it('mostra participação, consumo e o total do recorte em formato brasileiro', async () => {
    render(<Domicilios ano={2026} buscar={buscar()} />)
    const linha = await screen.findByTestId('linha-uni_60')
    expect(within(linha).getByText('8,4%')).toBeInTheDocument()
    expect(within(linha).getByText('115,7')).toBeInTheDocument()
    expect(within(screen.getByTestId('linha-mul_59')).getByText('sem dado')).toBeInTheDocument()
    expect(screen.getByTestId('total-recorte')).toHaveTextContent('21,3%')
  })

  it('esmaece as casas fora do filtro', async () => {
    const { container } = render(<Domicilios ano={2070} buscar={buscar()} />)
    await screen.findByText('35 de cada 100 domicílios')
    fireEvent.click(screen.getByRole('button', { name: 'Recorte 60+' }))
    expect(container.querySelectorAll('path.hs.dim')).toHaveLength(65)
  })

  it('destaca as casas da linha sob o cursor', async () => {
    const { container } = render(<Domicilios ano={2070} buscar={buscar()} />)
    fireEvent.mouseEnter(await screen.findByTestId('linha-cas_60'))
    expect(container.querySelector('.iso')).toHaveClass('hovering')
    expect(container.querySelectorAll('path.hs.hl')).toHaveLength(21)
  })

  it('avisa quando o ano não está na projeção', async () => {
    render(<Domicilios ano={2040} buscar={buscar()} />)
    expect(await screen.findByRole('heading', { name: 'Sem dado para 2040' })).toBeInTheDocument()
  })

  it('mostra o erro com o ano preservado', async () => {
    render(<Domicilios ano={2050} buscar={vi.fn().mockRejectedValue(new Error('A API respondeu com o código 503'))} />)
    expect(await screen.findByRole('alert')).toHaveTextContent('ano 2050')
  })
})
