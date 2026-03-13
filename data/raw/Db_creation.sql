-- USERS (freelancers and clients)
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL,       -- 'client' or 'freelancer'
    skills TEXT,             -- comma-separated for freelancers
    experience TEXT,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- JOBS (gigs posted by clients)
CREATE TABLE jobs (
    job_id SERIAL PRIMARY KEY,
    client_id INT REFERENCES users(user_id),
    title TEXT NOT NULL,
    description TEXT,
    skills_required TEXT,
    budget NUMERIC,
    status TEXT DEFAULT 'open', -- open, matched, in_progress, completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- APPLICATIONS (freelancers applying to jobs)
CREATE TABLE applications (
    application_id SERIAL PRIMARY KEY,
    job_id INT REFERENCES jobs(job_id),
    freelancer_id INT REFERENCES users(user_id),
    similarity_score NUMERIC,
    status TEXT DEFAULT 'applied',  -- applied, accepted, rejected
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ESCROW (locked client payments)
CREATE TABLE escrow (
    escrow_id SERIAL PRIMARY KEY,
    job_id INT REFERENCES jobs(job_id),
    amount NUMERIC NOT NULL,
    status TEXT DEFAULT 'pending',  -- pending, funded, released, disputed
    funded_at TIMESTAMP,
    released_at TIMESTAMP
);

-- TRANSACTIONS (money movements)
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    escrow_id INT REFERENCES escrow(escrow_id),
    payer_id INT REFERENCES users(user_id),
    receiver_id INT REFERENCES users(user_id),
    amount NUMERIC,
    status TEXT DEFAULT 'pending',  -- pending, success, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
