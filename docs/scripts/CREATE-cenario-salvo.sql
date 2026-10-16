-- Cenários calculados pelo Simulador, guardados para reaproveitar consultas (RF09).
-- Rodar no editor SQL do Supabase (PostgreSQL). A API grava e lê pela REST com a chave secreta.
--
-- Um cenário é identificado pelos parâmetros da consulta e pela versão do modelo. A versão muda
-- sempre que o cálculo ou as premissas mudarem (VERSAO_MODELO em backend/app/dominio.py); um
-- cenário de versão antiga não é encontrado pela consulta da versão atual, então nunca volta
-- como recuperado, e é recalculado e gravado com a versão nova.

create table if not exists public.cenario_salvo (
    id             bigint generated always as identity primary key,
    -- ano, faixa, arranjo, base, localidade, intensidade e k, como foram validados pela API
    parametros     jsonb       not null check (jsonb_typeof(parametros) = 'object'),
    versao_modelo  text        not null check (length(versao_modelo) > 0),
    -- a resposta do Simulador (SimulacaoResposta), sem o campo recuperado
    resultado      jsonb       not null check (jsonb_typeof(resultado) = 'object'),
    criado_em      timestamptz not null default now(),
    atualizado_em  timestamptz not null default now(),
    -- chave única: a igualdade de jsonb não depende da ordem das chaves
    constraint cenario_salvo_parametros_versao_unicos unique (parametros, versao_modelo)
);

comment on table public.cenario_salvo is
    'Cenários do Simulador já calculados (RF09), por parâmetros da consulta e versão do modelo';

-- atualizado_em acompanha cada regravação (recalcular=true)
create or replace function public.cenario_salvo_atualizado_em()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
    new.atualizado_em := now();
    return new;
end;
$$;

drop trigger if exists cenario_salvo_atualizado_em on public.cenario_salvo;
create trigger cenario_salvo_atualizado_em
    before update on public.cenario_salvo
    for each row execute function public.cenario_salvo_atualizado_em();

-- Segurança: RLS ligado e nenhuma política, então o acesso anônimo fica negado.
-- Só a chave secreta do back-end (que ignora o RLS) lê e grava.
alter table public.cenario_salvo enable row level security;
