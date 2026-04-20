-- MySQL migration for diseases table (embedding stored as JSON text).

CREATE TABLE IF NOT EXISTS diseases (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  symptoms TEXT NOT NULL,
  description TEXT NOT NULL,
  specialty VARCHAR(120) NOT NULL,
  embedding LONGTEXT NULL,
  INDEX idx_diseases_name (name),
  INDEX idx_diseases_specialty (specialty)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
