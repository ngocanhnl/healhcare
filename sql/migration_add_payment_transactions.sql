-- Add payment_transactions table (VNPay integration)

CREATE TABLE IF NOT EXISTS payment_transactions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  patient_id INT NOT NULL,
  schedule_id INT NOT NULL,
  vnp_txn_ref VARCHAR(64) NOT NULL UNIQUE,
  amount_vnd INT NOT NULL,
  status ENUM('PENDING','SUCCESS','FAILED') NOT NULL DEFAULT 'PENDING',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_payment_patient (patient_id),
  INDEX idx_payment_schedule (schedule_id),
  CONSTRAINT fk_payment_patient FOREIGN KEY (patient_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_payment_schedule FOREIGN KEY (schedule_id) REFERENCES schedules(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

