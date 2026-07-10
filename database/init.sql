CREATE DATABASE IF NOT EXISTS smart_care_training
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE smart_care_training;

CREATE TABLE IF NOT EXISTS students (
    student_id VARCHAR(16) PRIMARY KEY,
    student_name VARCHAR(32) NOT NULL,
    age INT NOT NULL,
    organization VARCHAR(64) NOT NULL,
    position VARCHAR(32) NOT NULL,
    platform VARCHAR(16) NOT NULL,
    enroll_date DATE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS courses (
    course_id VARCHAR(16) PRIMARY KEY,
    course_name VARCHAR(128) NOT NULL,
    category VARCHAR(32) NOT NULL,
    tag VARCHAR(32) NOT NULL,
    difficulty VARCHAR(16) NOT NULL,
    hours INT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS resources (
    resource_id VARCHAR(16) PRIMARY KEY,
    course_id VARCHAR(16) NOT NULL,
    resource_title VARCHAR(128) NOT NULL,
    format VARCHAR(24) NOT NULL,
    duration_minutes INT NOT NULL,
    terminal VARCHAR(16) NOT NULL,
    INDEX idx_resources_course (course_id),
    CONSTRAINT fk_resources_course FOREIGN KEY (course_id) REFERENCES courses(course_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS learning_events (
    event_id VARCHAR(20) PRIMARY KEY,
    student_id VARCHAR(16) NOT NULL,
    course_id VARCHAR(16) NOT NULL,
    resource_id VARCHAR(16) NOT NULL,
    event_date DATE NOT NULL,
    duration_minutes INT NOT NULL,
    progress_percent INT NOT NULL,
    completed TINYINT NOT NULL,
    device VARCHAR(16) NOT NULL,
    INDEX idx_events_student_course (student_id, course_id),
    INDEX idx_events_date (event_date),
    CONSTRAINT fk_events_student FOREIGN KEY (student_id) REFERENCES students(student_id),
    CONSTRAINT fk_events_course FOREIGN KEY (course_id) REFERENCES courses(course_id),
    CONSTRAINT fk_events_resource FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS assessment_scores (
    student_id VARCHAR(16) NOT NULL,
    course_id VARCHAR(16) NOT NULL,
    midterm_score DECIMAL(5, 2) NOT NULL,
    final_score DECIMAL(5, 2) NOT NULL,
    practical_score DECIMAL(5, 2) NOT NULL,
    attendance_rate DECIMAL(5, 2) NOT NULL,
    PRIMARY KEY (student_id, course_id),
    INDEX idx_scores_course (course_id),
    INDEX idx_scores_final (final_score),
    CONSTRAINT fk_scores_student FOREIGN KEY (student_id) REFERENCES students(student_id),
    CONSTRAINT fk_scores_course FOREIGN KEY (course_id) REFERENCES courses(course_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
