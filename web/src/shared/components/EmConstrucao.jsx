export default function EmConstrucao({ titulo, requisitos }) {
  return (
    <>
      <div className="vh">
        <div>
          <h1>{titulo}</h1>
          <p>Atende {requisitos}.</p>
        </div>
      </div>
      <section className="pan">
        <div className="pstate">
          <h3>Tela em construção</h3>
          <p>O endpoint desta tela ainda não foi definido no contrato da API. A referência visual está em prototipo/proced.html.</p>
        </div>
      </section>
    </>
  )
}
