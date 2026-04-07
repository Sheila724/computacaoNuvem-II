BEGIN;

-- 1) Corrige dados antigos nulos/vazios
UPDATE cliente
SET documento = '987.654.321-00'
WHERE documento IS NULL OR documento = '';

-- 2) Define valor padrao para novos registros
ALTER TABLE cliente
ALTER COLUMN documento SET DEFAULT '987.654.321-00';

-- 3) Impede null daqui pra frente
ALTER TABLE cliente
ALTER COLUMN documento SET NOT NULL;

COMMIT;
