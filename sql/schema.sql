-- ==========================================
-- Medical Platform - MySQL Schema (utf8mb4)
-- ==========================================

CREATE DATABASE IF NOT EXISTS medical_platform
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE medical_platform;

-- Users
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(80) NOT NULL UNIQUE,
  email VARCHAR(255) NULL,
  phone VARCHAR(20) NULL,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('PATIENT','DOCTOR','ADMIN') NOT NULL DEFAULT 'PATIENT',
  INDEX idx_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Hospitals
CREATE TABLE IF NOT EXISTS hospitals (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(160) NOT NULL UNIQUE,
  INDEX idx_hospitals_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Doctors
CREATE TABLE IF NOT EXISTS doctors (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL UNIQUE,
  specialty VARCHAR(120) NOT NULL,
  hospital_id INT NULL,
  description TEXT NULL,
  experience_years INT NOT NULL DEFAULT 0,
  INDEX idx_doctors_specialty (specialty),
  INDEX idx_doctors_hospital (hospital_id),
  CONSTRAINT fk_doctors_user FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_doctors_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
    ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Schedules
CREATE TABLE IF NOT EXISTS schedules (
  id INT AUTO_INCREMENT PRIMARY KEY,
  doctor_id INT NOT NULL,
  date DATE NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  is_available TINYINT(1) NOT NULL DEFAULT 1,
  INDEX idx_schedules_doctor (doctor_id),
  INDEX idx_schedules_date (date),
  INDEX idx_schedules_available (is_available),
  CONSTRAINT uq_doctor_slot UNIQUE (doctor_id, date, start_time, end_time),
  CONSTRAINT fk_schedules_doctor FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Weekly shifts (doctor availability by weekday)
CREATE TABLE IF NOT EXISTS weekly_shifts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  doctor_id INT NOT NULL,
  weekday TINYINT NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  INDEX idx_weekly_shifts_doctor (doctor_id),
  INDEX idx_weekly_shifts_weekday (weekday),
  INDEX idx_weekly_shifts_active (is_active),
  CONSTRAINT uq_weekly_shift UNIQUE (doctor_id, weekday, start_time, end_time),
  CONSTRAINT fk_weekly_shifts_doctor FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Appointments
CREATE TABLE IF NOT EXISTS appointments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  patient_id INT NOT NULL,
  doctor_id INT NOT NULL,
  schedule_id INT NOT NULL UNIQUE,
  booking_for VARCHAR(20) NOT NULL DEFAULT 'self',
  contact_fullname VARCHAR(80) NOT NULL,
  contact_email VARCHAR(255) NULL,
  contact_phone VARCHAR(20) NOT NULL,
  symptoms TEXT NULL,
  status ENUM('PENDING','CONFIRMED','CANCELLED') NOT NULL DEFAULT 'PENDING',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_appointments_patient (patient_id),
  INDEX idx_appointments_doctor (doctor_id),
  INDEX idx_appointments_booking_for (booking_for),
  INDEX idx_appointments_contact_phone (contact_phone),
  INDEX idx_appointments_status (status),
  INDEX idx_appointments_created (created_at),
  CONSTRAINT fk_appointments_patient FOREIGN KEY (patient_id) REFERENCES users(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_appointments_doctor FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_appointments_schedule FOREIGN KEY (schedule_id) REFERENCES schedules(id)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

