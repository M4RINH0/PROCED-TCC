import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { ARQUIVO_DADOS_INICIAIS, gerarDadosIniciais } from './src/services/dadosIniciais.js'

/* No build, grava em dist/ as respostas da API para a visão padrão de cada tela
   (src/services/dadosIniciais.js). Sem API acessível, o build segue e o site
   consulta a API normalmente. */
function dadosIniciais(api) {
  return {
    name: 'proced-dados-iniciais',
    apply: 'build',
    async generateBundle() {
      if (!api) {
        this.warn('VITE_API_URL não definida: o build segue sem os dados de abertura')
        return
      }
      const { dados, falhas } = await gerarDadosIniciais(api)
      const total = Object.keys(dados).length
      if (total === 0) {
        this.warn(`API inacessível (${falhas[0]}): o build segue sem os dados de abertura`)
        return
      }
      falhas.forEach((falha) => this.warn(`dados de abertura sem ${falha}`))
      this.emitFile({ type: 'asset', fileName: ARQUIVO_DADOS_INICIAIS, source: JSON.stringify(dados) })
      console.log(`dados de abertura: ${total} consultas gravadas em ${ARQUIVO_DADOS_INICIAIS}`)
    },
  }
}

export default defineConfig(({ mode }) => ({
  plugins: [react(), dadosIniciais(loadEnv(mode, process.cwd(), '').VITE_API_URL)],
  // porta fixa: a API só libera esta origem no CORS; se estiver ocupada, o Vite avisa em vez de trocar
  server: { port: 5173, strictPort: true },
  test: {
    environment: 'jsdom',
    setupFiles: ['./test/setup.js'],
    globals: true,
  },
}))
