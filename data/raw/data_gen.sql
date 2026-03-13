-- Generate 700 freelancers
INSERT INTO users (name, phone, role, skills, experience, location)
SELECT
    'Freelancer_' || g AS name,
    '+2547' || lpad((100000000 + g)::text, 9, '0') AS phone,
    'freelancer' AS role,
    string_agg(s.skill, ',') AS skills,
    CASE WHEN random() < 0.5 THEN 'beginner' ELSE 'intermediate' END AS experience,
    CASE WHEN random() < 0.7 THEN 'Nairobi' ELSE 'Mombasa' END AS location
FROM generate_series(1,700) AS g
CROSS JOIN LATERAL (
    SELECT skill
    FROM (VALUES
        ('python'),('pandas'),('data analysis'),('javascript'),('react'),('node'),
        ('sql'),('excel'),('tableau'),('figma'),('branding'),('graphic design')
    ) AS s(skill)
    ORDER BY random()
    LIMIT 3
) s
GROUP BY g;

---generate some sample jobs
-- Generate 500 jobs
INSERT INTO jobs (client_id, title, description, skills_required, budget)
SELECT 
    u.user_id AS client_id,
    'Job_' || g AS title,
    'Description for job ' || g AS description,
    string_agg(s.skill, ',') AS skills_required,
    (random()*500 + 20)::numeric(10,2) AS budget
FROM generate_series(1,500) AS g
JOIN users u ON u.role='client'
CROSS JOIN LATERAL (
    SELECT skill
    FROM (VALUES
        ('python'),('pandas'),('data analysis'),('javascript'),('react'),('node'),
        ('sql'),('excel'),('tableau'),('figma'),('branding'),('graphic design')
    ) AS s(skill)
    ORDER BY random()
    LIMIT 2
) s
GROUP BY g, u.user_id
ORDER BY random()
LIMIT 500;

-- Generate applications
INSERT INTO applications (job_id, freelancer_id, similarity_score)
SELECT
    j.job_id,
    f.user_id AS freelancer_id,
    ROUND(random()::numeric, 2) AS similarity_score  -- 0.00 to 1.00
FROM jobs j
JOIN users f ON f.role = 'freelancer'
WHERE random() < 0.2;  -- ~20% chance each freelancer applies to a job




