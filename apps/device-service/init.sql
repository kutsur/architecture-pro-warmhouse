CREATE TABLE IF NOT EXISTS devices (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    state VARCHAR(20) NOT NULL DEFAULT 'OFF',
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO devices (id, name, type, state, location) VALUES
    ('550e8400-e29b-41d4-a716-446655440001', 'Living Room Heater', 'heating', 'OFF', 'Living Room'),
    ('550e8400-e29b-41d4-a716-446655440002', 'Bedroom Heater', 'heating', 'OFF', 'Bedroom'),
    ('550e8400-e29b-41d4-a716-446655440003', 'Kitchen Heater', 'heating', 'OFF', 'Kitchen')
ON CONFLICT (id) DO NOTHING;
