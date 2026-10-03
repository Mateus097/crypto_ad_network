-- =============================================================================
-- ESTRUTURA DO BANCO DE DADOS - CRYPTO AD NETWORK
-- =============================================================================

-- Habilitar extensão para geração de UUIDs (Identificadores Únicos Universais)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- 1. TABELA: PUBLISHERS (Afiliados / Donos de Sites)
-- -----------------------------------------------------------------------------
CREATE TABLE publishers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,

    -- Carteira Polygon (USDT/USDC) com validação de formato EVM (0x + 40 chars hex)
    polygon_wallet VARCHAR(42) NOT NULL
        CHECK (polygon_wallet ~* '^0x[a-fA-F0-9]{40}$'),

    -- Controle Financeiro
    pending_balance_usd DECIMAL(12, 6) DEFAULT 0.000000
        CHECK (pending_balance_usd >= 0), -- Saldo acumulado do mês atual

    paid_balance_usd DECIMAL(12, 6) DEFAULT 0.000000
        CHECK (paid_balance_usd >= 0),    -- Total histórico já sacado

    status VARCHAR(20) DEFAULT 'ACTIVE'
        CHECK (status IN ('PENDING', 'ACTIVE', 'SUSPENDED', 'BANNED')),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 2. TABELA: WEBSITES (Sites/Blogs cadastrados pelos Publishers)
-- -----------------------------------------------------------------------------
CREATE TABLE websites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    publisher_id UUID NOT NULL REFERENCES publishers(id) ON DELETE CASCADE,
    domain VARCHAR(255) NOT NULL,
    category VARCHAR(50) DEFAULT 'GENERAL',
    status VARCHAR(20) DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 3. TABELA: IMPRESSION_LOGS (Histórico e Auditoria de Impressões)
-- -----------------------------------------------------------------------------
CREATE TABLE impression_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    publisher_id UUID NOT NULL REFERENCES publishers(id),
    website_id UUID REFERENCES websites(id) ON DELETE SET NULL,

    -- Dados do Tráfego para Antifraude
    user_ip VARCHAR(45) NOT NULL,
    user_agent TEXT NOT NULL,
    country_code VARCHAR(2) DEFAULT 'XX',

    -- Dados Financeiros da Impressão (6 casas decimais para precisão de centavos de dólar)
    gross_cpm_usd DECIMAL(8, 4) NOT NULL,        -- CPM retornado pela Ad Exchange externa
    publisher_revenue DECIMAL(12, 6) NOT NULL,    -- 80% repassado ao Publisher
    platform_revenue DECIMAL(12, 6) NOT NULL,     -- 20% margem da sua rede

    is_valid BOOLEAN DEFAULT TRUE,               -- Marcado como FALSE se for bot/fraude
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 4. TABELA: PAYOUT_TRANSACTIONS (Histórico de Saques na Polygon)
-- -----------------------------------------------------------------------------
CREATE TABLE payout_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    publisher_id UUID NOT NULL REFERENCES publishers(id),
    amount_usd DECIMAL(12, 6) NOT NULL CHECK (amount_usd > 0),
    recipient_wallet VARCHAR(42) NOT NULL,

    -- Hash da transação na blockchain Polygon para auditoria
    polygon_tx_hash VARCHAR(66) UNIQUE,

    status VARCHAR(20) DEFAULT 'PROCESSING'
        CHECK (status IN ('PENDING', 'PROCESSING', 'SUCCESS', 'FAILED')),

    error_message TEXT,
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- ÍNDICES DE ALTA PERFORMANCE (Para consultas em milhões de registros)
-- =============================================================================

-- Acelera a consulta de saldo e carregamento do painel do publisher
CREATE INDEX idx_publishers_wallet ON publishers(polygon_wallet);

-- Acelera relatórios e contagem antifraude por IP no mesmo dia
CREATE INDEX idx_impressions_ip_created ON impression_logs(user_ip, created_at);

-- Acelera o cálculo de saldo do mês por publisher
CREATE INDEX idx_impressions_publisher_valid ON impression_logs(publisher_id, is_valid, created_at);

-- Acelera consultas de histórico de saques
CREATE INDEX idx_payouts_publisher ON payout_transactions(publisher_id, status);