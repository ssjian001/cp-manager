-- CP Manager Database Schema
-- Based on AIAG Core Platform 1st Edition 2024

-- 1. Schema version control
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

-- 2. Application settings (including theme preference)
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- 3. Projects
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    part_number TEXT,
    part_name TEXT,
    supplier TEXT,
    supplier_code TEXT,
    contact_person TEXT,
    contact_phone TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 4. Control plans
CREATE TABLE IF NOT EXISTS control_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    cp_number TEXT,
    phase TEXT NOT NULL DEFAULT 'prototype'
        CHECK(phase IN ('prototype','pre_launch','production')),
    is_safe_launch INTEGER DEFAULT 0,
    safe_launch_start TEXT,
    safe_launch_end TEXT,
    safe_launch_duration_days INTEGER DEFAULT 90,
    safe_launch_fail_count INTEGER DEFAULT 0,
    safe_launch_exit_criteria TEXT,
    foundation_source_id INTEGER,
    status TEXT DEFAULT 'draft'
        CHECK(status IN ('draft','review','approved','obsolete')),
    core_team TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(project_id) REFERENCES projects(id),
    FOREIGN KEY(foundation_source_id) REFERENCES control_plans(id)
);

-- 5. Process steps
CREATE TABLE IF NOT EXISTS process_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    step_number TEXT NOT NULL,
    step_name TEXT NOT NULL,
    equipment TEXT,
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY(plan_id) REFERENCES control_plans(id) ON DELETE CASCADE
);

-- 6. Control plan items (characteristics)
CREATE TABLE IF NOT EXISTS cp_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    step_id INTEGER NOT NULL,
    plan_id INTEGER NOT NULL,
    char_number TEXT,
    char_type TEXT DEFAULT 'product'
        CHECK(char_type IN ('product','process')),
    char_description TEXT,
    special_classification TEXT DEFAULT 'none'
        CHECK(special_classification IN ('none','CC','SC','KPC','OSC','HI','custom')),
    specification TEXT,
    tolerance TEXT,
    measurement_method TEXT,
    gauge_id TEXT,
    sample_size TEXT,
    sample_frequency TEXT,
    control_method_type TEXT DEFAULT 'manual'
        CHECK(control_method_type IN ('SPC','EP','MP','visual','manual','auto')),
    ep_verification_freq TEXT,
    ep_verification_method TEXT,
    responsible TEXT,
    reaction_plan TEXT,
    notes TEXT,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY(step_id) REFERENCES process_steps(id) ON DELETE CASCADE,
    FOREIGN KEY(plan_id) REFERENCES control_plans(id) ON DELETE CASCADE
);

-- 7. Reaction plan templates
CREATE TABLE IF NOT EXISTS reaction_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    stop_process TEXT,
    product_disposition TEXT,
    notify_who TEXT,
    recovery_condition TEXT,
    is_default INTEGER DEFAULT 0
);

-- 8. Team members
CREATE TABLE IF NOT EXISTS team_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    role TEXT,
    department TEXT,
    FOREIGN KEY(plan_id) REFERENCES control_plans(id) ON DELETE CASCADE
);

-- 9. Approvals
CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    approval_type TEXT NOT NULL
        CHECK(approval_type IN ('prepared','reviewed','approved')),
    name TEXT NOT NULL,
    signed_at TEXT,
    FOREIGN KEY(plan_id) REFERENCES control_plans(id) ON DELETE CASCADE
);

-- 10. Change records
CREATE TABLE IF NOT EXISTS change_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    changed_by TEXT,
    FOREIGN KEY(plan_id) REFERENCES control_plans(id) ON DELETE CASCADE
);

-- Initial data
INSERT OR IGNORE INTO schema_version VALUES(1);
INSERT OR IGNORE INTO settings(key, value) VALUES('theme', 'light');
