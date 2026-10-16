/* Grupo de botões de escolha única */
export default function Segmentado({ rotulo, opcoes, valor, aoMudar }) {
  const id = `seg-${rotulo.toLowerCase().replace(/\W+/g, '-')}`
  return (
    <div className="fl fl-seg">
      <span className="flab" id={id}>
        {rotulo}
      </span>
      <div className="seg" role="group" aria-labelledby={id}>
        {opcoes.map((o) => (
          <button key={o.id} type="button" aria-pressed={valor === o.id} onClick={() => aoMudar(o.id)}>
            {o.rotulo}
          </button>
        ))}
      </div>
    </div>
  )
}
