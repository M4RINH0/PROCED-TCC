# Premissas

Toda premissa adotada onde faltar dado entra aqui, com fonte citável.

| Id | Premissa | Fonte | Onde é usada |
|---|---|---|---|
| P1 | Casal de idosos = domicílio de dois moradores (`Casal ou Dupla`) com chefe de 60 anos ou mais. O banco não traz a idade do cônjuge nem o parentesco, então duplas que não são casal também entram. | Estrutura da tabela `fato_consumo_domiciliar` (POF 2017 a 2018, IBGE) | Recorte mononuclear (`backend/app/dominio.py`) |
| P2 | Taxa de chefia constante: a proporção entre domicílios mononucleares com chefe na faixa x e a população da faixa x em 2018 se mantém nos anos projetados. `nDom_x,s = (n_x,POF / Pop_x,2018) * Pop_x,s` | POF 2017 a 2018 e Projeções da População (IBGE) | Cenário oficial (`ibge`) e, por faixa e arranjo, a composição dos domicílios (`/arranjos/composicao`), em `backend/app/services/panorama.py` e `backend/app/services/domicilios.py` |
| P3 | Médias sem peso amostral: a TEC de cada faixa é a média simples dos domicílios da amostra, porque o banco não traz o peso da POF. | Estrutura da tabela `fato_consumo_domiciliar` | TEC por faixa e por arranjo |
| P4 | A faixa de chefe "até 29" usa a população de 12 a 29 anos (12 é a menor idade de chefe na amostra). | `fato_consumo_domiciliar` | P2 |
| P5 | A faixa "80+" inclui a idade 90 da projeção, que agrega 90 anos ou mais. | `projecoes_populacao_idade` | Pirâmide e P2 |
| P6 | A TEC de cada faixa fica fixa nos níveis da POF 2017 a 2018; só a estrutura etária muda (padronização direta, eq:tbc-pd). | Metodologia do TCC | Cenário oficial |

Pendências de confirmação:
- Como o `consumo_total_kwh` do banco foi obtido a partir da POF e se é mensal.
- A formulação do cenário do modelo (`mod`), com a taxa de envelhecimento anual.
