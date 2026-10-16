import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../src/App.jsx'

describe('App', () => {
  beforeEach(() => {
    window.location.hash = ''
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))
  })

  it('abre no Panorama com a aba marcada', () => {
    render(<App />)
    expect(screen.getByRole('heading', { level: 1, name: 'Panorama da projeção' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Panorama' })).toHaveAttribute('aria-current', 'page')
  })

  it.each([
    ['Domicílios', 'Domicílios por arranjo'],
    ['Estrutura etária', 'Estrutura etária'],
    ['Simulador', 'Simulador de cenário'],
    ['Comparar', 'Comparar grupos'],
  ])('navega para a aba %s', (aba, titulo) => {
    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: aba }))
    expect(screen.getByRole('heading', { level: 1, name: titulo })).toBeInTheDocument()
    expect(window.location.hash).not.toBe('')
  })

  it('não mostra o selo nem qualquer menção a machine learning', () => {
    render(<App />)
    expect(document.body.textContent).not.toMatch(/machine learning|Random Forest|Gradient Boosting/i)
  })

  it('alterna o tema no elemento raiz', () => {
    render(<App />)
    const antes = document.documentElement.dataset.theme
    fireEvent.click(screen.getByRole('button', { name: /tema/i }))
    expect(document.documentElement.dataset.theme).not.toBe(antes)
  })

  it('não exibe mais o selo de dados ilustrativos', () => {
    render(<App />)
    expect(screen.queryByText('Dados ilustrativos')).not.toBeInTheDocument()
  })
})

/* ---------- parâmetros de simulação globais e filtro de localidade ---------- */

const REGIOES = {
  padrao: 'Brasil',
  regioes: [{ nome: 'Nordeste', estados: [{ sigla: 'BA', nome: 'Bahia' }, { sigla: 'PE', nome: 'Pernambuco' }] }],
}

function apiFalsa() {
  const urls = []
  const fetch = vi.fn((url) => {
    urls.push(String(url))
    if (String(url).includes('/localidades')) return Promise.resolve({ ok: true, json: () => Promise.resolve(REGIOES) })
    return new Promise(() => {})  // as consultas de dados ficam pendentes: aqui só importam as URLs
  })
  return { urls, fetch }
}

const deslizar = (rotulo, valor) => fireEvent.change(screen.getByLabelText(rotulo), { target: { value: String(valor) } })
const aba = (nome) => fireEvent.click(screen.getByRole('button', { name: nome }))

describe('App: parâmetros de simulação e localidade', () => {
  beforeEach(() => {
    window.location.hash = ''
  })

  it('os parâmetros são compartilhados entre as páginas e preservados ao trocar de aba', () => {
    vi.stubGlobal('fetch', apiFalsa().fetch)
    render(<App />)
    deslizar('Velocidade do envelhecimento (k)', 1.3)
    deslizar('Intensidade da mudança de arranjos', 1.1)
    for (const nome of ['Domicílios', 'Estrutura etária', 'Simulador', 'Panorama']) {
      aba(nome)
      expect(screen.getByLabelText('Velocidade do envelhecimento (k)')).toHaveValue('1.3')
      expect(screen.getByLabelText('Intensidade da mudança de arranjos')).toHaveValue('1.1')
      expect(screen.getByTestId('rotulo-simulacao')).toHaveTextContent('Simulação')
    }
  })

  it('na Estrutura etária a intensidade fica desabilitada e explica por quê', () => {
    vi.stubGlobal('fetch', apiFalsa().fetch)
    render(<App />)
    aba('Estrutura etária')
    expect(screen.getByLabelText('Intensidade da mudança de arranjos')).toBeDisabled()
    expect(screen.getByText(/a mudança de arranjos não altera esta página/)).toBeInTheDocument()
    expect(screen.getByLabelText('Velocidade do envelhecimento (k)')).toBeEnabled()
  })

  it('restaurar o padrão volta os dois controles e tira o rótulo de simulação', () => {
    vi.stubGlobal('fetch', apiFalsa().fetch)
    render(<App />)
    deslizar('Velocidade do envelhecimento (k)', 0.7)
    aba('Domicílios')
    fireEvent.click(screen.getByRole('button', { name: 'Restaurar padrão' }))
    expect(screen.getByLabelText('Velocidade do envelhecimento (k)')).toHaveValue('1')
    expect(screen.getByLabelText('Intensidade da mudança de arranjos')).toHaveValue('0.6')
    expect(screen.queryByTestId('rotulo-simulacao')).not.toBeInTheDocument()
  })

  it('espera o fim dos ajustes antes de consultar (debounce)', async () => {
    const api = apiFalsa()
    vi.stubGlobal('fetch', api.fetch)
    render(<App />)
    const series = () => api.urls.filter((u) => u.includes('/projecoes/serie'))
    await waitFor(() => expect(series()).toHaveLength(1))
    for (const v of [0.7, 0.8, 0.9, 1.0]) deslizar('Intensidade da mudança de arranjos', v)
    await waitFor(() => expect(series()).toHaveLength(2), { timeout: 2000 })
    await new Promise((r) => setTimeout(r, 600))
    expect(series()).toHaveLength(2)  // uma consulta só, com o valor final
    expect(series()[1]).toContain('intensidade=1&k=1')
  })

  it('envia k e intensidade em todas as chamadas afetadas', async () => {
    const api = apiFalsa()
    vi.stubGlobal('fetch', api.fetch)
    render(<App />)
    deslizar('Velocidade do envelhecimento (k)', 1.2)
    deslizar('Intensidade da mudança de arranjos', 1.1)
    const ultima = (trecho) => api.urls.filter((u) => u.includes(trecho)).at(-1) ?? ''
    await waitFor(() => expect(ultima('/projecoes/serie')).toContain('intensidade=1.1&k=1.2'), { timeout: 2000 })
    aba('Domicílios')
    await waitFor(() => expect(ultima('/arranjos/composicao')).toContain('intensidade=1.1&k=1.2'))
    aba('Estrutura etária')
    await waitFor(() => expect(ultima('/estrutura-etaria/piramides')).toContain('k=1.2'))
    expect(ultima('/estrutura-etaria/piramides')).not.toContain('intensidade')
    expect(ultima('/estrutura-etaria/consumo-chefe')).not.toMatch(/intensidade|k=/)
    aba('Simulador')
    await waitFor(() => expect(ultima('/simulador')).toContain('intensidade=1.1&k=1.2'))
  })

  it('trocar a localidade dispara novas chamadas com o parâmetro certo em todas as páginas', async () => {
    const api = apiFalsa()
    vi.stubGlobal('fetch', api.fetch)
    render(<App />)
    const regiao = screen.getByLabelText('Região')
    await waitFor(() => expect(regiao.querySelectorAll('option')).toHaveLength(2))
    fireEvent.change(regiao, { target: { value: 'Nordeste' } })
    await waitFor(() => expect(api.urls.at(-1)).toContain('/projecoes/serie?recorte=todos_domicilios&localidade=Nordeste'))
    expect([...screen.getByLabelText('Estado').options].map((o) => o.value)).toEqual(['Nordeste', 'BA', 'PE'])
    fireEvent.change(screen.getByLabelText('Estado'), { target: { value: 'PE' } })
    await waitFor(() => expect(api.urls.at(-1)).toContain('localidade=PE'))
    aba('Domicílios')
    await waitFor(() => expect(api.urls.filter((u) => u.includes('/arranjos/composicao')).at(-1)).toContain('localidade=PE'))
    aba('Estrutura etária')
    await waitFor(() => expect(api.urls.filter((u) => u.includes('/piramides')).at(-1)).toContain('localidade=PE'))
    aba('Simulador')
    await waitFor(() => expect(api.urls.filter((u) => u.includes('/simulador')).at(-1)).toContain('localidade=PE'))
  })
})
