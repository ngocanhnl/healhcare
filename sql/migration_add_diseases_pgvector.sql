-- PostgreSQL + pgvector migration for RAG diseases index
-- Run on PostgreSQL database only.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS diseases (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  symptoms TEXT NOT NULL,
  description TEXT NOT NULL,
  specialty VARCHAR(120) NOT NULL,
  embedding VECTOR(1536)
);

CREATE INDEX IF NOT EXISTS idx_diseases_specialty ON diseases (specialty);
CREATE INDEX IF NOT EXISTS idx_diseases_embedding
  ON diseases USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
