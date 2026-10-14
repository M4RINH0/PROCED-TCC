-- Tabela das POFs 2002 a 2003 e 2008 a 2009, usada para estimar a tendência dos arranjos (premissa P13).
-- Rodar no editor SQL do Supabase (PostgreSQL). Não altera a fato_consumo_domiciliar (POF 2017 a 2018).
-- A carga é feita depois pelo ETL: python -m etl.historica (na pasta backend/).

create table if not exists public.fato_consumo_pof_historica (
    ano_pof                smallint         not null check (ano_pof in (2002, 2008)),
    sigla_uf               char(2)          not null,
    id_domicilio           text             not null,
    qtd_moradores          smallint         not null check (qtd_moradores >= 1),
    arranjo_familiar       text             not null
        check (arranjo_familiar in ('Unipessoal (Mononuclear)', 'Casal ou Dupla', 'Multipessoal (3+)')),
    idade_chefe            smallint         not null check (idade_chefe >= 0),
    is_60_mais             boolean          not null,
    consumo_total_kwh      double precision not null check (consumo_total_kwh >= 0),
    consumo_per_capita_kwh double precision not null check (consumo_per_capita_kwh >= 0),
    peso_final             double precision not null check (peso_final > 0),
    kwh_imputado           boolean          not null,
    energia_rede_geral     boolean          not null,
    primary key (ano_pof, id_domicilio)
);

comment on table public.fato_consumo_pof_historica is
    'POF 2002 a 2003 e 2008 a 2009 (IBGE), um domicílio com conta de luz por linha; tendência dos arranjos (P13)';

-- Segurança: RLS ligado e nenhuma política, então o acesso anônimo fica negado.
-- Só a chave secreta do back-end (que ignora o RLS) lê e grava.
alter table public.fato_consumo_pof_historica enable row level security;
