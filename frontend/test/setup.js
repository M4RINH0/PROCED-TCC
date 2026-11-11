import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { limparCache } from '../src/services/cache.js'

/* o cache de respostas vive no módulo: cada teste começa sem nada guardado */
afterEach(() => limparCache())
