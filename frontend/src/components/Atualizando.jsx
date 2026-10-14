/* Aviso de consulta em andamento com dados antigos na tela: eles ficam esmaecidos e
   este aviso diz para onde a tela está indo, em vez de mostrar números antigos com o nome novo */
export default function Atualizando({ ativo, destino }) {
  if (!ativo) return null
  return (
    <p className="atualizando" role="status" data-testid="atualizando">
      Atualizando para {destino}…
    </p>
  )
}
