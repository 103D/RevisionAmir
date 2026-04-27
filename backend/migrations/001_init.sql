-- Create filials table
CREATE TABLE IF NOT EXISTS filials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    first_revision_date DATE NOT NULL,
    previous_revision_date DATE,
    next_revision_date DATE,
    shortage NUMERIC DEFAULT 0,
    revision_dates TEXT[] DEFAULT '[]',
    revision_statuses JSONB DEFAULT '{}',
    revision_shortages JSONB DEFAULT '{}',
    next_revision_status TEXT DEFAULT 'planned',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create holidays table
CREATE TABLE IF NOT EXISTS holidays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL UNIQUE,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_filials_next_revision ON filials(next_revision_date);
CREATE INDEX IF NOT EXISTS idx_holidays_date ON holidays(date);
