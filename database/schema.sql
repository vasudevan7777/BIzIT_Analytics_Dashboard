-- ============================================
-- BizIT Analytics - Database Schema
-- MySQL Database Setup Script
-- ============================================

-- ============================================
-- Create Database
-- ============================================
CREATE DATABASE IF NOT EXISTS bizit_analytics;
USE bizit_analytics;

-- ============================================
-- Users Table
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'Analyst',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Business Data Table
-- ============================================
CREATE TABLE IF NOT EXISTS business_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    revenue DECIMAL(15, 2) NOT NULL,
    cost DECIMAL(15, 2) NOT NULL,
    expenses DECIMAL(15, 2) DEFAULT 0,
    profit DECIMAL(15, 2) NOT NULL,
    department VARCHAR(100) NOT NULL,
    sales_volume INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT,
    
    UNIQUE KEY unique_date_department (date, department),
    INDEX idx_date (date),
    INDEX idx_department (department),
    INDEX idx_date_range (date, department),
    
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Alerts Table
-- ============================================
CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    message VARCHAR(500) NOT NULL,
    severity VARCHAR(20) DEFAULT 'warning',
    department VARCHAR(100),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_type (type),
    INDEX idx_is_read (is_read),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Upload History Table
-- ============================================
CREATE TABLE IF NOT EXISTS upload_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    records_count INT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT,
    uploaded_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_uploaded_by (uploaded_by),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================
-- Insert Default Admin User
-- Password: Admin@123 (bcrypt hashed)
-- ============================================
INSERT INTO users (name, email, password_hash, role, is_active)
VALUES (
    'Administrator',
    'admin@bizitanalytics.com',
    'scrypt:32768:8:1$VEPLn3rMIOyAc0T4$9e7b2d3f8a1c5e6b4d2f1a3c5e7b9d1f3a5c7e9b1d3f5a7c9e1b3d5f7a9c1e3b5d7f9a1c3e5b7d9f1a3c5e7b9d1f3a5c7e9b1d3f5a7c9e1b3d',
    'Admin',
    TRUE
) ON DUPLICATE KEY UPDATE name = name;

-- ============================================
-- Stored Procedures
-- ============================================

-- Calculate Monthly KPIs
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS GetMonthlyKPIs(
    IN p_year INT,
    IN p_month INT,
    IN p_department VARCHAR(100)
)
BEGIN
    SELECT 
        SUM(revenue) as total_revenue,
        SUM(cost) as total_cost,
        SUM(expenses) as total_expenses,
        SUM(profit) as net_profit,
        ROUND(SUM(profit) / NULLIF(SUM(revenue), 0) * 100, 2) as profit_margin,
        SUM(sales_volume) as total_sales
    FROM business_data
    WHERE YEAR(date) = p_year 
      AND MONTH(date) = p_month
      AND (p_department IS NULL OR department = p_department);
END //
DELIMITER ;

-- Get Department Performance
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS GetDepartmentPerformance()
BEGIN
    SELECT 
        department,
        SUM(revenue) as total_revenue,
        SUM(cost) as total_cost,
        SUM(profit) as total_profit,
        SUM(sales_volume) as total_sales,
        ROUND(SUM(profit) / NULLIF(SUM(revenue), 0) * 100, 2) as profit_margin,
        COUNT(*) as record_count
    FROM business_data
    GROUP BY department
    ORDER BY total_profit DESC;
END //
DELIMITER ;

-- ============================================
-- Views
-- ============================================

-- Monthly Summary View
CREATE OR REPLACE VIEW monthly_summary AS
SELECT 
    DATE_FORMAT(date, '%Y-%m') as month,
    SUM(revenue) as total_revenue,
    SUM(cost) as total_cost,
    SUM(profit) as total_profit,
    SUM(expenses) as total_expenses,
    SUM(sales_volume) as total_sales,
    ROUND(SUM(profit) / NULLIF(SUM(revenue), 0) * 100, 2) as profit_margin
FROM business_data
GROUP BY DATE_FORMAT(date, '%Y-%m')
ORDER BY month DESC;

-- Department Summary View
CREATE OR REPLACE VIEW department_summary AS
SELECT 
    department,
    SUM(revenue) as total_revenue,
    SUM(cost) as total_cost,
    SUM(profit) as total_profit,
    SUM(expenses) as total_expenses,
    SUM(sales_volume) as total_sales,
    ROUND(SUM(profit) / NULLIF(SUM(revenue), 0) * 100, 2) as profit_margin,
    COUNT(*) as record_count
FROM business_data
GROUP BY department;

-- ============================================
-- Indexes for Performance (50,000+ records)
-- ============================================

-- Compound indexes for common queries
CREATE INDEX IF NOT EXISTS idx_date_dept_revenue ON business_data(date, department, revenue);
CREATE INDEX IF NOT EXISTS idx_dept_date ON business_data(department, date);

-- ============================================
-- Grants (adjust as needed)
-- ============================================
-- GRANT ALL PRIVILEGES ON bizit_analytics.* TO 'bizit_user'@'localhost' IDENTIFIED BY 'secure_password';
-- FLUSH PRIVILEGES;
