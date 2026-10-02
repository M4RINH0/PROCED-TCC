/* Barra que sempre começa no zero; a largura é a proporção do valor sobre o máximo da tabela */
export default function BarraHorizontal({ valor, maximo, destaque = false }) {
  const proporcao = maximo > 0 && valor > 0 ? Math.min(1, valor / maximo) : 0
  return (
    <span className="barra" aria-hidden="true">
      <span className={destaque ? 'barra-v on' : 'barra-v'} style={{ width: `${proporcao * 100}%` }} />
    </span>
  )
}
