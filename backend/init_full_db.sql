-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- vocabularies 表
CREATE TABLE IF NOT EXISTS vocabularies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word VARCHAR(255) NOT NULL,
    phonetic VARCHAR(100),
    part_of_speech JSON,
    definitions JSON,
    english_definition TEXT,
    examples JSON,
    etymology VARCHAR(255),
    difficulty_level VARCHAR(50),
    frequency_level INTEGER,
    related_words JSON,
    synonyms JSON,
    antonyms JSON,
    collocations JSON,
    extra_data JSON,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- contents 表
CREATE TABLE IF NOT EXISTS contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    content_type VARCHAR(50) NOT NULL,
    difficulty_level VARCHAR(50) NOT NULL,
    exam_type VARCHAR(50),
    topic VARCHAR(100),
    tags JSON,
    content_text TEXT,
    media_url VARCHAR(500),
    duration INTEGER,
    word_count INTEGER,
    vector_id VARCHAR(100),
    embedding_text TEXT,
    knowledge_points JSON,
    extra_metadata JSON,
    is_published BOOLEAN NOT NULL DEFAULT false,
    is_featured BOOLEAN NOT NULL DEFAULT false,
    sort_order INTEGER NOT NULL DEFAULT 0,
    view_count INTEGER NOT NULL DEFAULT 0,
    favorite_count INTEGER NOT NULL DEFAULT 0,
    created_by UUID,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    published_at TIMESTAMP
);

-- lesson_plan_templates 表
CREATE TABLE IF NOT EXISTS lesson_plan_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    level VARCHAR(10) NOT NULL,
    target_exam VARCHAR(50),
    template_structure JSONB NOT NULL,
    is_system BOOLEAN NOT NULL DEFAULT false,
    usage_count INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_by UUID,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- lesson_plans 表
CREATE TABLE IF NOT EXISTS lesson_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    teacher_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    level VARCHAR(10) NOT NULL,
    duration INTEGER NOT NULL,
    target_exam VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    ai_generation_params JSONB,
    objectives JSONB,
    vocabulary JSONB,
    grammar_points JSONB,
    teaching_structure JSONB,
    leveled_materials JSONB,
    exercises JSONB,
    ppt_outline JSONB,
    resources JSONB,
    teaching_notes TEXT,
    generation_time_ms INTEGER,
    last_generated_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- students 表
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    student_no VARCHAR(50),
    grade VARCHAR(50),
    class_id UUID,
    parent_ids UUID[],
    target_exam VARCHAR(100),
    target_score INTEGER,
    study_goal TEXT,
    current_cefr_level VARCHAR(10),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- teachers 表
CREATE TABLE IF NOT EXISTS teachers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    specialization VARCHAR(100)[],
    qualification JSON,
    bio TEXT,
    organization_id UUID,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- content_vocabulary 表
CREATE TABLE IF NOT EXISTS content_vocabulary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL,
    vocabulary_id UUID NOT NULL,
    context_sentence TEXT,
    context_position JSON,
    is_key_vocabulary BOOLEAN NOT NULL DEFAULT false,
    is_exam_point BOOLEAN NOT NULL DEFAULT false,
    priority INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- knowledge_graphs 表
CREATE TABLE IF NOT EXISTS knowledge_graphs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL,
    nodes JSONB,
    edges JSONB,
    abilities JSONB,
    cefr_level VARCHAR(10),
    exam_coverage JSONB,
    ai_analysis JSONB,
    last_ai_analysis_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_vocabularies_word ON vocabularies(word);
CREATE INDEX IF NOT EXISTS ix_vocabularies_id ON vocabularies(id);

CREATE INDEX IF NOT EXISTS ix_contents_content_type ON contents(content_type);
CREATE INDEX IF NOT EXISTS ix_contents_difficulty_level ON contents(difficulty_level);
CREATE INDEX IF NOT EXISTS ix_contents_exam_type ON contents(exam_type);
CREATE INDEX IF NOT EXISTS ix_contents_topic ON contents(topic);
CREATE INDEX IF NOT EXISTS ix_contents_is_published ON contents(is_published);
CREATE INDEX IF NOT EXISTS ix_contents_is_featured ON contents(is_featured);
CREATE INDEX IF NOT EXISTS ix_contents_vector_id ON contents(vector_id);
CREATE INDEX IF NOT EXISTS ix_contents_id ON contents(id);
CREATE INDEX IF NOT EXISTS ix_contents_created_by ON contents(created_by);

CREATE INDEX IF NOT EXISTS ix_lesson_plan_templates_level ON lesson_plan_templates(level);
CREATE INDEX IF NOT EXISTS ix_lesson_plan_templates_is_active ON lesson_plan_templates(is_active);
CREATE INDEX IF NOT EXISTS ix_lesson_plan_templates_id ON lesson_plan_templates(id);

CREATE INDEX IF NOT EXISTS ix_lesson_plans_teacher_id ON lesson_plans(teacher_id);
CREATE INDEX IF NOT EXISTS ix_lesson_plans_level ON lesson_plans(level);
CREATE INDEX IF NOT EXISTS ix_lesson_plans_status ON lesson_plans(status);
CREATE INDEX IF NOT EXISTS ix_lesson_plans_topic ON lesson_plans(topic);
CREATE INDEX IF NOT EXISTS ix_lesson_plans_id ON lesson_plans(id);

CREATE INDEX IF NOT EXISTS ix_students_user_id ON students(user_id);
CREATE INDEX IF NOT EXISTS ix_students_student_no ON students(student_no);
CREATE INDEX IF NOT EXISTS ix_students_id ON students(id);

CREATE INDEX IF NOT EXISTS ix_teachers_user_id ON teachers(user_id);
CREATE INDEX IF NOT EXISTS ix_teachers_id ON teachers(id);
CREATE INDEX IF NOT EXISTS ix_teachers_organization_id ON teachers(organization_id);

CREATE INDEX IF NOT EXISTS ix_content_vocabulary_content_id ON content_vocabulary(content_id);
CREATE INDEX IF NOT EXISTS ix_content_vocabulary_vocabulary_id ON content_vocabulary(vocabulary_id);

CREATE INDEX IF NOT EXISTS ix_knowledge_graphs_student_id ON knowledge_graphs(student_id);
CREATE INDEX IF NOT EXISTS ix_knowledge_graphs_id ON knowledge_graphs(id);

-- 外键约束
ALTER TABLE contents ADD CONSTRAINT fk_contents_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE lesson_plan_templates ADD CONSTRAINT fk_lesson_plan_templates_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE lesson_plans ADD CONSTRAINT fk_lesson_plans_teacher_id FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE students ADD CONSTRAINT fk_students_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE teachers ADD CONSTRAINT fk_teachers_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE teachers ADD CONSTRAINT fk_teachers_organization_id FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE SET NULL;
ALTER TABLE content_vocabulary ADD CONSTRAINT fk_content_vocabulary_content_id FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE;
ALTER TABLE content_vocabulary ADD CONSTRAINT fk_content_vocabulary_vocabulary_id FOREIGN KEY (vocabulary_id) REFERENCES vocabularies(id) ON DELETE CASCADE;
ALTER TABLE knowledge_graphs ADD CONSTRAINT fk_knowledge_graphs_student_id FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;

-- 乐观锁支持 (使用 version 字段)
ALTER TABLE users ADD COLUMN version INTEGER NOT NULL DEFAULT 0;
ALTER TABLE organizations ADD COLUMN version INTEGER NOT NULL DEFAULT 0;
ALTER TABLE vocabularies ADD COLUMN version INTEGER NOT NULL DEFAULT 0;
ALTER TABLE contents ADD COLUMN version INTEGER NOT NULL DEFAULT 0;
ALTER TABLE lesson_plan_templates ADD COLUMN version INTEGER NOT NULL DEFAULT 0;
ALTER TABLE lesson_plans ADD COLUMN version INTEGER NOT NULL DEFAULT 0;
ALTER TABLE students ADD COLUMN version INTEGER NOT NULL DEFAULT 0;
ALTER TABLE teachers ADD COLUMN version INTEGER NOT NULL DEFAULT 0;
ALTER TABLE content_vocabulary ADD COLUMN version INTEGER NOT NULL DEFAULT 0;
ALTER TABLE knowledge_graphs ADD COLUMN version INTEGER NOT NULL DEFAULT 0;
