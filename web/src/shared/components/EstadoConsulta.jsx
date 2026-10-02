/* Carregamento e erro no contexto da tela, com os parâmetros preservados (UC01, UC04) */
export default function EstadoConsulta({ status, erro, parametros, aoTentarDeNovo, temDados }) {
  if (status === 'carregando' && !temDados) {
    return (
      <div aria-busy="true" aria-label="Carregando dados">
        <div className="skel" style={{ width: '40%' }} />
        <div className="skel" style={{ width: '70%' }} />
        <p className="pf">A primeira consulta pode levar alguns segundos enquanto a API lê o banco.</p>
      </div>
    )
  }
  if (status === 'erro') {
    return (
      <div className="pstate erro" role="alert">
        <h3>Não foi possível carregar os dados</h3>
        <p>
          {erro?.message}. Os parâmetros foram mantidos: {parametros}.
        </p>
        <button type="button" className="btn" onClick={aoTentarDeNovo}>
          Tentar novamente
        </button>
      </div>
    )
  }
  return null
}
