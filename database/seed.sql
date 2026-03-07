-- HR-RAG Seed Data
-- Version: 1.0.0

-- Insert sample user (password: demo123)
-- Using bcrypt hash for 'demo123'
INSERT INTO users (id, email, password_hash, created_at, api_keys_json) VALUES
(1, 'demo@hr-rag.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4bKH.zU0YL2K3LWG', NOW(), '{"openai": "sk-demo-key", "qdrant": "demo-qdrant-key"}');

-- Insert sample chat sessions
INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at) VALUES
(1, 1, 'HR Policy Questions', NOW() - INTERVAL 7 DAY, NOW() - INTERVAL 1 DAY),
(2, 1, 'Employee Benefits Inquiry', NOW() - INTERVAL 3 DAY, NOW() - INTERVAL 2 HOUR),
(3, 1, 'Onboarding Process', NOW() - INTERVAL 1 DAY, NOW() - INTERVAL 30 MINUTE);

-- Insert sample chat messages
INSERT INTO chat_messages (id, session_id, role, content, tokens, created_at) VALUES
-- Session 1: HR Policy Questions
(1, 1, 'system', 'You are an HR assistant helping with company policies.', NULL, NOW() - INTERVAL 7 DAY),
(2, 1, 'user', 'What is the company vacation policy?', 25, NOW() - INTERVAL 7 DAY + INTERVAL 1 MINUTE),
(3, 1, 'assistant', 'Our company offers 20 days of paid vacation per year, increasing to 25 days after 3 years of service. Vacation requests should be submitted at least 2 weeks in advance through the HR portal.', 85, NOW() - INTERVAL 7 DAY + INTERVAL 2 MINUTE),
(4, 1, 'user', 'How about sick leave?', 15, NOW() - INTERVAL 6 DAY),
(5, 1, 'assistant', 'Employees receive 10 days of paid sick leave per year. For extended illness, additional unpaid leave may be granted with medical documentation.', 72, NOW() - INTERVAL 6 DAY + INTERVAL 1 MINUTE),

-- Session 2: Employee Benefits
(6, 2, 'system', 'You are an HR assistant specializing in employee benefits.', NULL, NOW() - INTERVAL 3 DAY),
(7, 2, 'user', 'What health benefits are available?', 20, NOW() - INTERVAL 3 DAY),
(8, 2, 'assistant', 'We offer comprehensive health insurance including medical, dental, and vision coverage. The company covers 80% of premiums for employees and 60% for dependents.', 95, NOW() - INTERVAL 3 DAY + INTERVAL 2 MINUTE),
(9, 2, 'user', 'Is there a 401k match?', 10, NOW() - INTERVAL 2 DAY),
(10, 2, 'assistant', 'Yes! We match 100% of contributions up to 6% of your salary. Vesting is immediate upon hire.', 55, NOW() - INTERVAL 2 DAY + INTERVAL 1 MINUTE),

-- Session 3: Onboarding
(11, 3, 'system', 'You are an HR assistant helping new employees with onboarding.', NULL, NOW() - INTERVAL 1 DAY),
(12, 3, 'user', 'What documents do I need to bring on my first day?', 30, NOW() - INTERVAL 1 DAY),
(13, 3, 'assistant', 'Please bring: 1) Government-issued photo ID, 2) Social Security card or passport, 3) Completed I-9 form, 4) Voided check for direct deposit, 5) Emergency contact information.', 120, NOW() - INTERVAL 1 DAY + INTERVAL 2 MINUTE),
(14, 3, 'user', 'What should I expect on day one?', 20, NOW() - INTERVAL 30 MINUTE),
(15, 3, 'assistant', 'Day one includes: Welcome orientation (9 AM), IT setup and badge photo, Meet your team lunch, HR benefits enrollment, and workspace tour. Dress code is business casual.', 95, NOW() - INTERVAL 29 MINUTE);

-- Insert sample projects
INSERT INTO projects (id, user_id, name, description, created_at) VALUES
(1, 1, 'Employee Handbook 2026', 'Complete rewrite of employee handbook with new policies', NOW() - INTERVAL 30 DAY),
(2, 1, 'Benefits Guide', 'Comprehensive guide to employee benefits and perks', NOW() - INTERVAL 14 DAY),
(3, 1, 'Onboarding Documents', 'New hire onboarding checklist and procedures', NOW() - INTERVAL 7 DAY);

-- Insert sample project documents
INSERT INTO project_documents (id, project_id, filename, content_hash, vector_ids, created_at) VALUES
(1, 1, 'vacation_policy.md', 'a1b2c3d4e5f6g7h8i9j0', '["vec_001", "vec_002"]', NOW() - INTERVAL 25 DAY),
(2, 1, 'sick_leave_policy.md', 'b2c3d4e5f6g7h8i9j0k1', '["vec_003"]', NOW() - INTERVAL 20 DAY),
(3, 2, 'health_insurance_summary.md', 'c3d4e5f6g7h8i9j0k1l2', '["vec_004", "vec_005"]', NOW() - INTERVAL 10 DAY),
(4, 2, '401k_plan_details.md', 'd4e5f6g7h8i9j0k1l2m3', '["vec_006"]', NOW() - INTERVAL 5 DAY),
(5, 3, 'new_hire_checklist.md', 'e5f6g7h8i9j0k1l2m3n4', '["vec_007", "vec_008"]', NOW() - INTERVAL 3 DAY),
(6, 3, 'first_day_agenda.md', 'f6g7h8i9j0k1l2m3n4o5', '["vec_009"]', NOW() - INTERVAL 1 DAY);

-- Insert sample vector metadata
INSERT INTO vector_metadata (id, document_id, collection_name, point_id, chunk_text, metadata_json, created_at) VALUES
(1, 1, 'hr_documents', 'vec_001', 'Vacation Policy: Employees are entitled to 20 days of paid vacation per year...', '{"source": "vacation_policy.md", "chunk": 1}', NOW() - INTERVAL 25 DAY),
(2, 1, 'hr_documents', 'vec_002', 'After 3 years of continuous service, vacation days increase to 25 days...', '{"source": "vacation_policy.md", "chunk": 2}', NOW() - INTERVAL 25 DAY),
(3, 2, 'hr_documents', 'vec_003', 'Sick Leave: 10 days of paid sick leave annually...', '{"source": "sick_leave_policy.md", "chunk": 1}', NOW() - INTERVAL 20 DAY),
(4, 3, 'hr_documents', 'vec_004', 'Health Insurance: Medical, dental, and vision coverage available...', '{"source": "health_insurance_summary.md", "chunk": 1}', NOW() - INTERVAL 10 DAY),
(5, 3, 'hr_documents', 'vec_005', 'Company covers 80% of premiums for employees...', '{"source": "health_insurance_summary.md", "chunk": 2}', NOW() - INTERVAL 10 DAY),
(6, 4, 'hr_documents', 'vec_006', '401k Plan: 100% match up to 6% of salary...', '{"source": "401k_plan_details.md", "chunk": 1}', NOW() - INTERVAL 5 DAY),
(7, 5, 'hr_documents', 'vec_007', 'New Hire Checklist: Bring ID, SS card, I-9 form...', '{"source": "new_hire_checklist.md", "chunk": 1}', NOW() - INTERVAL 3 DAY),
(8, 5, 'hr_documents', 'vec_008', 'Complete tax forms and direct deposit setup...', '{"source": "new_hire_checklist.md", "chunk": 2}', NOW() - INTERVAL 3 DAY),
(9, 6, 'hr_documents', 'vec_009', 'First Day Agenda: Orientation at 9 AM, IT setup...', '{"source": "first_day_agenda.md", "chunk": 1}', NOW() - INTERVAL 1 DAY);

-- Insert sample API keys
INSERT INTO api_keys (id, user_id, key_hash, name, rate_limit, is_active, created_at) VALUES
(1, 1, '$2b$12$hashed_key_placeholder_1', 'Development Key', 1000, TRUE, NOW() - INTERVAL 30 DAY),
(2, 1, '$2b$12$hashed_key_placeholder_2', 'Production Key', 5000, TRUE, NOW() - INTERVAL 14 DAY);
