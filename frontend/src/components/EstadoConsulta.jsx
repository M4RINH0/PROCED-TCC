import Icone from './Icone.jsx'

/* Carregamento e erro no contexto da tela, com os parâmetros preservados (UC01, UC04).
   Ocupa a área do gráfico, como no protótipo. */
export default function EstadoConsulta({ status, erro, parametros, aoTentarDeNovo, temDados, mudo = false }) {
  if (status === 'carregando' && !temDados) {
    return (
      <div className="pskel" aria-busy="true" aria-label="Carregando dados">
        <div className="skel" style={{ width: '32%' }} />
        <div className="skel sk-big" />
        <div className="skel" style={{ width: '58%', marginBottom: 0 }} />
      </div>
    )
  }
  if (status === 'erro') {
    if (mudo) {
      return (
        <div className="pstate mute">
          <p>Aguardando dados</p>
        </div>
      )
    }
    return (
      <div className="pstate" role="alert">
        <h3>
          <Icone nome="alert" />
          Não foi possível carregar os dados
        </h3>
        <p>
          {erro?.message}. Os parâmetros foram mantidos: <b>{parametros}</b>.
        </p>
        <button type="button" className="btn" onClick={aoTentarDeNovo}>
          <Icone nome="refresh" />
          Tentar novamente
        </button>
      </div>
    )
  }
  return null
}
