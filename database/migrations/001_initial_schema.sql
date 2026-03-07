-- Migration: 001_initial_schema
-- Description: Create initial HR-RAG database schema
-- Created: 2026-03-07

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    api_keys_json JSON DEFAULT NULL,
    INDEX idx_email (email),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create chat_sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    title VARCHAR(500) NOT NULL DEFAULT 'New Chat',
    created_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    updated_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create chat_messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT UNSIGNED NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,
    tokens INT UNSIGNED DEFAULT NULL,
    created_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create project_documents table
CREATE TABLE IF NOT EXISTS project_documents (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT UNSIGNED NOT NULL,
    filename VARCHAR(500) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    vector_ids JSON DEFAULT NULL,
    created_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_id (project_id),
    INDEX idx_content_hash (content_hash),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create vector_metadata table
CREATE TABLE IF NOT EXISTS vector_metadata (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    document_id BIGINT UNSIGNED NOT NULL,
    collection_name VARCHAR(255) NOT NULL,
    point_id VARCHAR(255) NOT NULL,
    chunk_text TEXT,
    metadata_json JSON DEFAULT NULL,
    created_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    FOREIGN KEY (document_id) REFERENCES project_documents(id) ON DELETE CASCADE,
    INDEX idx_document_id (document_id),
    INDEX idx_collection_name (collection_name),
    INDEX idx_point_id (point_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create api_keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL DEFAULT 'Default Key',
    rate_limit INT UNSIGNED DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at DATETIME(3) DEFAULT NULL,
    created_at DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_key_hash (key_hash),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
