# Metodologia Científica e Formulação Matemática

O **PROCED** fundamenta-se na demografia formal e na economia da energia, adotando a técnica da **Padronização Direta de Taxas** (*Direct Standardization*) combinada ao **Método das Taxas de Chefia** (*Headship Rate Method*) e à modelagem log-linear de transição de estruturas domiciliares.

Este documento formaliza as equações matemáticas, premissas de derivação e métodos de decomposição empregados no motor analítico (`backend/app/calculo.py`).

---

## 1. A Taxa Bruta de Consumo Padronizada (TBC)

A Taxa Bruta de Consumo (TBC) per capita observada em um dado período reflete tanto os hábitos individuais de consumo de cada grupo populacional quanto a composição etária e domiciliar da sociedade.

Para isolar as mudanças demográficas futuras mantendo constantes os padrões intrínsecos de consumo observados na POF 2017-2018 (Premissa P6), a TBC padronizada no ano projetado $s \in [2026, 2070]$ é definida como:

$$\text{TBC}_{\text{padronizada}}(s) = \sum_{c \in \mathcal{C}} w_c(s) \cdot \overline{y}_c$$

Onde:
* $\mathcal{C}$ é o conjunto das células sociodemográficas formadas pelo produto cartesiano de 7 faixas etárias do chefe e 3 tipos de arranjo familiar (21 células no total).
* $\overline{y}_c$ é o consumo médio per capita observado na célula $c$ na POF 2017-2018 ponderado pelo plano amostral:
  $$\overline{y}_c = \frac{\sum_{i \in c} \text{peso}_i \cdot \text{consumo\_per\_capita}_i}{\sum_{i \in c} \text{peso}_i}$$
* $w_c(s)$ é a proporção de domicílios da célula $c$ no ano $s$:
  $$w_c(s) = \frac{\text{nDom}_c(s)}{\sum_{c' \in \mathcal{C}} \text{nDom}_{c'}(s)}$$

---

## 2. Método das Taxas de Chefia e Projeção de Domicílios

### 2.1. Taxa de Chefia Total Constante por Faixa Etária (Premissa P2)
Na POF 2017-2018 (ano médio 2018), calcula-se a taxa de propensão à chefia de domicílio para cada faixa etária $x$:

$$\text{chefia}_x = \frac{\sum_{i \in \text{faixa } x} \text{peso}_i}{\text{Pop}_{x, 2018}}$$

Onde $\text{Pop}_{x, 2018}$ representa a população residente na faixa $x$ projetada pelo IBGE em 2018 para a localidade (sexo "Ambos").

A quantidade total de domicílios chefiados por pessoas na faixa etária $x$ no ano projetado $s$ é dada por:

$$\text{nDom}_x(s) = \text{chefia}_x \cdot \text{Pop}_x(s)$$

---

### 2.2. Modelagem da Transição dos Arranjos Familiares (Premissa P13)

Historicamente, a proporção de domicílios com múltiplos moradores vem recuando no Brasil, enquanto domicílios unipessoais e de duas pessoas crescem de forma sistemática.

Para projetar a divisão dos domicílios da faixa $x$ entre os 3 arranjos $a \in \{\text{unipessoal}, \text{casal/dupla}, \text{multipessoal}\}$, utiliza-se um modelo multinomial log-linear ancorado nas três edições da POF (2002.5, 2008.5 e 2017.5). Adotando o arranjo multipessoal como categoria de referência:

$$\ln\left(\frac{\pi_{x, \text{uni}}(s)}{\pi_{x, \text{multi}}(s)}\right) = \ln\left(\frac{\pi_{x, \text{uni}}(2017.5)}{\pi_{x, \text{multi}}(2017.5)}\right) + \lambda \cdot \beta_{x, \text{uni}} \cdot (s - 2017.5)$$

$$\ln\left(\frac{\pi_{x, \text{casal}}(s)}{\pi_{x, \text{multi}}(s)}\right) = \ln\left(\frac{\pi_{x, \text{casal}}(2017.5)}{\pi_{x, \text{multi}}(2017.5)}\right) + \lambda \cdot \beta_{x, \text{casal}} \cdot (s - 2017.5)$$

Onde:
* $\beta_{x, a}$ é a inclinação da reta de mínimos quadrados estimada a partir das três edições históricas da POF.
* $\lambda \in [0.0, 1.5]$ é o parâmetro de **intensidade** da tendência.
* As proporções projetadas $\pi_{x, a}(s)$ são recuperadas pela função exponencial e normalizadas para que somem exatamente 1.
* A quantidade de domicílios na célula $(x, a)$ é então:
  $$\text{nDom}_{x, a}(s) = \text{nDom}_x(s) \cdot \pi_{x, a}(s)$$

#### Calibração da Intensidade Padrão ($\lambda = 0.6$) por Validação Fora do Tempo
Uma validação cruzada temporal (*backtesting*) foi conduzida estimando-se a inclinação apenas com as POFs de 2002 e 2008 para prever as proporções reais observadas na POF de 2017. O valor de $\lambda$ que minimizou o erro médio absoluto ponderado foi **$\lambda = 0.56$** (arredondado para **$0.6$**).

Com $\lambda = 0.6$, o erro médio absoluto caiu de 3,67 pontos percentuais (sob hipótese de arranjos congelados, $\lambda = 0$) para apenas 1,46 ponto percentual.

---

## 3. Controle da Velocidade de Envelhecimento ($k$) (Premissa P14)

O parâmetro $k \in [0.5, 1.5]$ (padrão $1.0$) permite modular a velocidade com que a estrutura de idades da população se afasta do perfil de 2026:

$$p_x(s; k) = p_x(2026) + k \cdot [p_x(s) - p_x(2026)]$$

Onde:
* $p_x(s)$ é a proporção original da faixa $x$ na projeção oficial do IBGE.
* Valores negativos são truncados a zero com piso, e o vetor de proporções é renormalizado para somar 1.
* A população ajustada da faixa é:
  $$\text{Pop}_x(s; k) = p_x(s; k) \cdot \text{Pop}_{\text{total}}(s)$$

Quando $k = 1.0$, o modelo reproduz exatamente a trajetória oficial do IBGE.

---

## 4. Moradores Médios e Consumo por Pessoa (Premissa P11)

O número médio ponderado de residentes de cada célula $\overline{m}_c$ é fixado no padrão observado da POF 2017-2018. O total de moradores projetados no recorte é:

$$\text{Moradores}(s) = \sum_{c \in \mathcal{C}} \text{nDom}_c(s) \cdot \overline{m}_c$$

O consumo médio por pessoa é calculado dividindo-se o consumo total não calibrado pelo volume de moradores projetados:

$$\text{ConsumoPorPessoa}(s) = \frac{\sum_{c \in \mathcal{C}} \text{nDom}_c(s) \cdot \overline{y}_{\text{dom}, c}}{\text{Moradores}(s)}$$

---

## 5. Calibração do Consumo Residencial Total (Premissa P12)

Os moradores projetados pela soma das células podem divergir ligeiramente da projeção oficial de população do IBGE devido à dinâmica de chefia. No cenário principal `taxas`, os moradores projetados situam-se 2,65% abaixo da população em 2026 e 1,33% acima em 2070.

Para assegurar compatibilidade absoluta com os agregados demográficos oficiais do país, define-se o **Fator de Calibração**:

$$\Phi(s) = \frac{\text{População Oficial IBGE}(s)}{\sum_{c} \text{nDom}_c(s) \cdot \overline{m}_c}$$

O **Consumo Residencial Total Calibrado** (em kWh/mês) passa a ser:

$$\text{ConsumoTotalCalibrado}(s) = \text{ConsumoPorPessoa}(s) \cdot \text{População Oficial IBGE}(s)$$

Esta formulação possui uma propriedade analítica fundamental: **elimina a dependência da cobertura amostral da POF (Premissa P9)**, pois calibra diretamente o consumo por pessoa expandido à totalidade da população recenseada.

---

## 6. Decomposição Analítica dos Três Efeitos

Para responder com precisão científica quanto do consumo futuro se deve à mudança na pirâmide de idades e quanto decorre da transição de arranjos familiares, o PROCED define três cenários canônicos:

1. **Cenário Principal (`taxas`):** Método das taxas com tendência dos arranjos ($\lambda = 0.6$).
2. **Cenário de Arranjos Fixos (`taxas_arranjos_fixos`):** Método das taxas com proporções de arranjo congeladas no valor de 2026.
3. **Cenário Contrafactual (`contrafactual`):** O número total de domicílios evolui proporcionalmente à população, mas a distribuição entre as 21 células $(x, a)$ permanece congelada no padrão de 2026 (Premissa P10).

A decomposição aditiva opera em qualquer métrica (TBC, consumo total calibrado ou participação):

$$\begin{aligned}
\text{Efeito Idade} &= \text{Cenário}_{\text{taxas\_arranjos\_fixos}} - \text{Cenário}_{\text{contrafactual}} \\
\text{Efeito Arranjos} &= \text{Cenário}_{\text{taxas}} - \text{Cenário}_{\text{taxas\_arranjos\_fixos}} \\
\text{Efeito Envelhecimento} &= \text{Cenário}_{\text{taxas}} - \text{Cenário}_{\text{contrafactual}}
\end{aligned}$$

Propriedade de fechamento exato:

$$\text{Efeito Envelhecimento} \equiv \text{Efeito Idade} + \text{Efeito Arranjos}$$
