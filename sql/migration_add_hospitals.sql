-- One-time migration to normalize hospitals (MySQL 8+)
-- - Creates hospitals table
-- - Adds doctors.hospital_id
-- - Optional: migrates legacy doctors.hospital_name -> hospitals + hospital_id

USE medical_platform;

CREATE TABLE IF NOT EXISTS hospitals (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(160) NOT NULL UNIQUE,
  INDEX idx_hospitals_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Add column if missing
ALTER TABLE doctors
  ADD COLUMN IF NOT EXISTS hospital_id INT NULL,
  ADD INDEX IF NOT EXISTS idx_doctors_hospital (hospital_id);

-- Optional legacy migration (safe even if column doesn't exist in some dumps)
-- If your existing schema has doctors.hospital_name, uncomment this block:
-- INSERT IGNORE INTO hospitals(name)
-- SELECT DISTINCT hospital_name
-- FROM doctors
-- WHERE hospital_name IS NOT NULL AND hospital_name <> '';
--
-- UPDATE doctors d
-- JOIN hospitals h ON h.name = d.hospital_name
-- SET d.hospital_id = h.id
-- WHERE d.hospital_id IS NULL;

-- Add FK (guarded by checking existing constraint manually if needed)
-- MySQL doesn't support IF NOT EXISTS for constraints; run once.
ALTER TABLE doctors
  ADD CONSTRAINT fk_doctors_hospital
  FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
  ON DELETE SET NULL ON UPDATE CASCADE;

