/* Fonte de cada consulta, igual à que a API devolve no campo `fonte`. O rodapé usa estes textos
   enquanto a resposta não chega ou quando a consulta falha, para citar as mesmas fontes do estado
   normal. O teste backend/test/test_fontes_front.py confere que cada texto é igual ao da API. */
export const FONTE_PANORAMA = 'POF 2002 a 2003, 2008 a 2009 e 2017 a 2018 e Projeções da População (IBGE)'
export const FONTE_COMPOSICAO =
  'POF 2002 a 2003, 2008 a 2009 e 2017 a 2018 e Projeções da População (IBGE); taxa de chefia de 2018 constante por faixa e tendência dos arranjos'
export const FONTE_PIRAMIDE = 'Projeções da População (IBGE)'
export const FONTE_CONSUMO_CHEFE = 'POF 2017 a 2018 (IBGE), média ponderada pelo peso amostral'
export const FONTE_SIMULADOR =
  'POF 2017 a 2018 (média ponderada pelo peso amostral), tendência das POFs 2002 a 2003 e 2008 a 2009 e Projeções da População (IBGE)'
