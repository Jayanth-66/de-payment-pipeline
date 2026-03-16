CREATE TABLE IF NOT EXISTS payment_metrics (
    bank_code TEXT,
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    total_amount DOUBLE PRECISION,
    success_count BIGINT,
    failed_count BIGINT
);