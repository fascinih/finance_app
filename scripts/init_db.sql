-- Finance App Database Initialization Script
-- Configurações iniciais e dados padrão

-- Configurar timezone
SET timezone = 'America/Sao_Paulo';

-- Criar schema principal se não existir
CREATE SCHEMA IF NOT EXISTS finance;

-- Configurar search_path
ALTER DATABASE finance_app SET search_path TO finance, public;

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Configurações de performance
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET track_io_timing = on;
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Recarregar configuração
SELECT pg_reload_conf();

-- Função para atualizar timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Função para gerar slugs
CREATE OR REPLACE FUNCTION generate_slug(input_text TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN lower(
        regexp_replace(
            regexp_replace(
                unaccent(input_text), 
                '[^a-zA-Z0-9\s]', '', 'g'
            ), 
            '\s+', '-', 'g'
        )
    );
END;
$$ LANGUAGE plpgsql;

-- Função para calcular estatísticas de categoria
CREATE OR REPLACE FUNCTION update_category_stats(category_id INTEGER)
RETURNS VOID AS $$
BEGIN
    UPDATE categories SET
        transaction_count = (
            SELECT COUNT(*) 
            FROM transactions 
            WHERE category_id = update_category_stats.category_id
        ),
        total_amount = (
            SELECT COALESCE(SUM(amount), 0) 
            FROM transactions 
            WHERE category_id = update_category_stats.category_id
        ),
        avg_amount = (
            SELECT COALESCE(AVG(amount), 0) 
            FROM transactions 
            WHERE category_id = update_category_stats.category_id
        ),
        last_transaction_date = (
            SELECT MAX(date) 
            FROM transactions 
            WHERE category_id = update_category_stats.category_id
        )
    WHERE id = category_id;
END;
$$ LANGUAGE plpgsql;

-- Função para detectar transações recorrentes
CREATE OR REPLACE FUNCTION detect_recurring_transactions()
RETURNS INTEGER AS $$
DECLARE
    recurring_count INTEGER := 0;
BEGIN
    -- Detectar transações com mesmo valor e descrição similar em intervalos regulares
    WITH recurring_candidates AS (
        SELECT 
            t1.id,
            t1.description,
            t1.amount,
            COUNT(*) OVER (PARTITION BY t1.description, t1.amount) as occurrence_count,
            LAG(t1.date) OVER (PARTITION BY t1.description, t1.amount ORDER BY t1.date) as prev_date,
            t1.date - LAG(t1.date) OVER (PARTITION BY t1.description, t1.amount ORDER BY t1.date) as days_diff
        FROM transactions t1
        WHERE t1.is_recurring = false
    )
    UPDATE transactions 
    SET 
        is_recurring = true,
        recurring_pattern = CASE 
            WHEN rc.days_diff BETWEEN 28 AND 32 THEN 'monthly'
            WHEN rc.days_diff BETWEEN 6 AND 8 THEN 'weekly'
            WHEN rc.days_diff BETWEEN 13 AND 16 THEN 'biweekly'
            WHEN rc.days_diff BETWEEN 89 AND 93 THEN 'quarterly'
            ELSE 'irregular'
        END
    FROM recurring_candidates rc
    WHERE transactions.id = rc.id
    AND rc.occurrence_count >= 3
    AND rc.days_diff IS NOT NULL;
    
    GET DIAGNOSTICS recurring_count = ROW_COUNT;
    RETURN recurring_count;
END;
$$ LANGUAGE plpgsql;

-- Inserir categorias padrão do sistema brasileiro
INSERT INTO categories (name, description, category_type, color, icon, is_system, keywords, sort_order) VALUES
-- Receitas
('Salário', 'Salário e remuneração', 'income', '#4CAF50', 'work', true, '["salario", "salário", "remuneracao", "remuneração", "pagamento"]', 1),
('Freelance', 'Trabalhos autônomos', 'income', '#8BC34A', 'freelance', true, '["freelance", "autonomo", "autônomo", "consultoria"]', 2),
('Investimentos', 'Rendimentos de investimentos', 'income', '#2196F3', 'trending_up', true, '["dividendo", "rendimento", "juros", "aplicacao", "aplicação"]', 3),
('Outros Rendimentos', 'Outras fontes de renda', 'income', '#00BCD4', 'attach_money', true, '["renda", "rendimento", "receita"]', 4),

-- Despesas Essenciais
('Moradia', 'Aluguel, financiamento, condomínio', 'expense', '#F44336', 'home', true, '["aluguel", "condominio", "condomínio", "financiamento", "iptu", "energia", "agua", "água", "gas", "gás"]', 10),
('Alimentação', 'Supermercado, feira, restaurantes', 'expense', '#FF9800', 'restaurant', true, '["supermercado", "mercado", "feira", "restaurante", "lanchonete", "padaria", "acougue", "açougue"]', 11),
('Transporte', 'Combustível, transporte público, manutenção', 'expense', '#9C27B0', 'directions_car', true, '["combustivel", "combustível", "gasolina", "etanol", "metro", "metrô", "onibus", "ônibus", "uber", "99", "taxi"]', 12),
('Saúde', 'Plano de saúde, medicamentos, consultas', 'expense', '#E91E63', 'local_hospital', true, '["plano", "saude", "saúde", "medico", "médico", "farmacia", "farmácia", "medicamento", "consulta"]', 13),
('Educação', 'Escola, faculdade, cursos', 'expense', '#3F51B5', 'school', true, '["escola", "faculdade", "universidade", "curso", "mensalidade", "material"]', 14),

-- Despesas Pessoais
('Vestuário', 'Roupas, calçados, acessórios', 'expense', '#795548', 'checkroom', true, '["roupa", "calcado", "calçado", "sapato", "camisa", "calca", "calça", "vestido"]', 20),
('Lazer', 'Entretenimento, viagens, hobbies', 'expense', '#FF5722', 'sports_esports', true, '["cinema", "teatro", "show", "viagem", "hotel", "passeio", "diversao", "diversão"]', 21),
('Beleza', 'Cabeleireiro, cosméticos, estética', 'expense', '#E91E63', 'face', true, '["cabeleireiro", "salao", "salão", "estetica", "estética", "cosmetico", "cosmético", "perfume"]', 22),
('Tecnologia', 'Eletrônicos, software, internet', 'expense', '#607D8B', 'devices', true, '["celular", "computador", "internet", "software", "netflix", "spotify", "aplicativo"]', 23),

-- Serviços Financeiros
('Bancos e Taxas', 'Tarifas bancárias, juros, taxas', 'expense', '#424242', 'account_balance', true, '["tarifa", "taxa", "juros", "anuidade", "cartao", "cartão", "banco"]', 30),
('Seguros', 'Seguro de vida, auto, residencial', 'expense', '#37474F', 'security', true, '["seguro", "seguradora", "apolice", "apólice"]', 31),

-- Transferências
('Transferência Entre Contas', 'Movimentação entre contas próprias', 'transfer', '#9E9E9E', 'swap_horiz', true, '["transferencia", "transferência", "pix", "ted", "doc"]', 40),
('Empréstimos', 'Empréstimos dados ou recebidos', 'transfer', '#757575', 'compare_arrows', true, '["emprestimo", "empréstimo", "financiamento"]', 41)

ON CONFLICT DO NOTHING;

-- Inserir subcategorias
INSERT INTO categories (name, description, category_type, parent_id, level, color, icon, is_system, keywords, sort_order) VALUES
-- Subcategorias de Moradia
('Aluguel', 'Pagamento de aluguel', 'expense', (SELECT id FROM categories WHERE name = 'Moradia'), 1, '#F44336', 'home', true, '["aluguel"]', 1),
('Condomínio', 'Taxa de condomínio', 'expense', (SELECT id FROM categories WHERE name = 'Moradia'), 1, '#F44336', 'apartment', true, '["condominio", "condomínio", "taxa condominial"]', 2),
('Energia Elétrica', 'Conta de luz', 'expense', (SELECT id FROM categories WHERE name = 'Moradia'), 1, '#FFC107', 'flash_on', true, '["energia", "luz", "eletrica", "elétrica", "cemig", "cpfl", "enel"]', 3),
('Água e Esgoto', 'Conta de água', 'expense', (SELECT id FROM categories WHERE name = 'Moradia'), 1, '#2196F3', 'water_drop', true, '["agua", "água", "esgoto", "sabesp", "copasa"]', 4),
('Gás', 'Conta de gás', 'expense', (SELECT id FROM categories WHERE name = 'Moradia'), 1, '#FF5722', 'local_gas_station', true, '["gas", "gás", "comgas"]', 5),

-- Subcategorias de Alimentação
('Supermercado', 'Compras no supermercado', 'expense', (SELECT id FROM categories WHERE name = 'Alimentação'), 1, '#FF9800', 'shopping_cart', true, '["supermercado", "mercado", "extra", "carrefour", "pao", "pão", "acucar", "açúcar"]', 1),
('Restaurantes', 'Refeições fora de casa', 'expense', (SELECT id FROM categories WHERE name = 'Alimentação'), 1, '#FF9800', 'restaurant', true, '["restaurante", "lanchonete", "fast food", "delivery"]', 2),
('Delivery', 'Pedidos por aplicativo', 'expense', (SELECT id FROM categories WHERE name = 'Alimentação'), 1, '#FF9800', 'delivery_dining', true, '["ifood", "uber eats", "rappi", "delivery"]', 3),

-- Subcategorias de Transporte
('Combustível', 'Gasolina, etanol, diesel', 'expense', (SELECT id FROM categories WHERE name = 'Transporte'), 1, '#9C27B0', 'local_gas_station', true, '["combustivel", "combustível", "gasolina", "etanol", "diesel", "posto"]', 1),
('Transporte Público', 'Metrô, ônibus, trem', 'expense', (SELECT id FROM categories WHERE name = 'Transporte'), 1, '#9C27B0', 'directions_bus', true, '["metro", "metrô", "onibus", "ônibus", "trem", "bilhete"]', 2),
('Aplicativos de Transporte', 'Uber, 99, taxi', 'expense', (SELECT id FROM categories WHERE name = 'Transporte'), 1, '#9C27B0', 'local_taxi', true, '["uber", "99", "taxi", "cabify"]', 3),
('Manutenção Veicular', 'Revisão, peças, oficina', 'expense', (SELECT id FROM categories WHERE name = 'Transporte'), 1, '#9C27B0', 'build', true, '["oficina", "revisao", "revisão", "peca", "peça", "pneu", "oleo", "óleo"]', 4)

ON CONFLICT DO NOTHING;

-- Criar índices adicionais para performance
CREATE INDEX IF NOT EXISTS idx_transactions_date_desc ON transactions (date DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_amount_abs ON transactions (abs(amount));
CREATE INDEX IF NOT EXISTS idx_transactions_description_trgm ON transactions USING gin (description gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_categories_name_trgm ON categories USING gin (name gin_trgm_ops);

-- Criar triggers para atualizar timestamps
CREATE TRIGGER update_transactions_updated_at 
    BEFORE UPDATE ON transactions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at 
    BEFORE UPDATE ON categories 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Criar view para relatórios
CREATE OR REPLACE VIEW v_transaction_summary AS
SELECT 
    t.id,
    t.date,
    t.amount,
    t.description,
    t.transaction_type,
    c.name as category_name,
    c.category_type,
    CASE 
        WHEN t.amount > 0 THEN 'credit'
        ELSE 'debit'
    END as flow_type,
    ABS(t.amount) as absolute_amount
FROM transactions t
LEFT JOIN categories c ON t.category_id = c.id;

-- Criar view para análise mensal
CREATE OR REPLACE VIEW v_monthly_summary AS
SELECT 
    DATE_TRUNC('month', date) as month,
    c.category_type,
    c.name as category_name,
    COUNT(*) as transaction_count,
    SUM(ABS(amount)) as total_amount,
    AVG(ABS(amount)) as avg_amount
FROM transactions t
LEFT JOIN categories c ON t.category_id = c.id
GROUP BY DATE_TRUNC('month', date), c.category_type, c.name
ORDER BY month DESC, total_amount DESC;

-- Log de inicialização
INSERT INTO pg_stat_statements_reset();

-- Mensagem de sucesso
DO $$
BEGIN
    RAISE NOTICE 'Finance App database initialized successfully!';
    RAISE NOTICE 'Categories created: %', (SELECT COUNT(*) FROM categories);
    RAISE NOTICE 'Extensions installed: uuid-ossp, pg_stat_statements, btree_gin, pg_trgm';
    RAISE NOTICE 'Performance optimizations applied';
END $$;

