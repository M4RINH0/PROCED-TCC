import Icone from './Icone.jsx'

/* Aviso de baixa confiabilidade: a API marca a célula com menos de 30 domicílios na amostra da POF.
   celulas: [{ faixa, arranjo, domicilios_amostra, baixa_confiabilidade }] (opcional, para listar quais) */
export default function AvisoAmostra({ ativo, celulas = [] }) {
  if (!ativo) return null
  const pequenas = celulas.filter((c) => c.baixa_confiabilidade)
  return (
    <div className="aviso-amostra" role="note" data-testid="aviso-amostra">
      <Icone nome="alert" />
      <span>
        Baixa confiabilidade: há célula com menos de 30 domicílios na amostra da POF nesta localidade.
        {pequenas.length > 0 && (
          <>
            {' '}
            {pequenas
              .map((c) => `${c.faixa}, ${c.arranjo.toLowerCase()}: ${c.domicilios_amostra.toLocaleString('pt-BR')}`)
              .join('; ')}
            .
          </>
        )}
      </span>
    </div>
  )
}
