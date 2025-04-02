-- Schema pour la base de données de l'Assistant Juridique IA
-- PostgreSQL avec extension pgvector pour le stockage des embeddings

-- Activation de l'extension pgvector pour les embeddings
CREATE EXTENSION IF NOT EXISTS pgvector;

-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_professional BOOLEAN NOT NULL DEFAULT FALSE,
    profession VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Table des domaines juridiques
CREATE TABLE IF NOT EXISTS legal_domains (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Table des sources juridiques (lois, jurisprudence, etc.)
CREATE TABLE IF NOT EXISTS legal_sources (
    id VARCHAR(50) PRIMARY KEY,
    title TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    date DATE NOT NULL,
    url TEXT,
    metadata JSONB,
    embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index sur le type de source pour les filtres courants
CREATE INDEX IF NOT EXISTS idx_legal_sources_type ON legal_sources(type);

-- Index vectoriel pour la recherche sémantique
CREATE INDEX IF NOT EXISTS idx_legal_sources_embedding ON legal_sources USING ivfflat (embedding vector_cosine_ops);

-- Table des requêtes des utilisateurs
CREATE TABLE IF NOT EXISTS user_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    query TEXT NOT NULL,
    domain VARCHAR(50),
    context TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    anonymized BOOLEAN NOT NULL DEFAULT FALSE
);

-- Table des réponses générées
CREATE TABLE IF NOT EXISTS responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID NOT NULL REFERENCES user_queries(id),
    introduction TEXT NOT NULL,
    legal_framework TEXT NOT NULL,
    application TEXT NOT NULL,
    exceptions TEXT,
    recommendations JSONB NOT NULL,
    sources JSONB NOT NULL,
    date_updated DATE NOT NULL,
    disclaimer TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Table des sources utilisées pour chaque réponse
CREATE TABLE IF NOT EXISTS response_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    response_id UUID NOT NULL REFERENCES responses(id),
    source_id VARCHAR(50) NOT NULL REFERENCES legal_sources(id),
    relevance_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Table de feedback sur les réponses
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    response_id UUID NOT NULL REFERENCES responses(id),
    user_id UUID REFERENCES users(id),
    rating INTEGER NOT NULL,
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Insertion des domaines juridiques de base
INSERT INTO legal_domains (name, description) VALUES
('fiscal', 'Droit fiscal: impôts, taxes, contentieux fiscal'),
('travail', 'Droit du travail: contrats, licenciements, conventions collectives'),
('affaires', 'Droit des affaires: sociétés, commercial, concurrence'),
('famille', 'Droit de la famille: mariage, divorce, filiation, successions'),
('immobilier', 'Droit immobilier: propriété, baux, copropriété'),
('consommation', 'Droit de la consommation: protection du consommateur'),
('penal', 'Droit pénal: infractions, procédures pénales'),
('autre', 'Autres domaines juridiques')
ON CONFLICT (name) DO NOTHING; 