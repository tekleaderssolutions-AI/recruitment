import psycopg2
from db import get_connection

def init_db():
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # 1. Enable pgvector extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # 2. Create memories table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id UUID PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT,
                text TEXT,
                embedding vector(768),
                metadata JSONB,
                canonical_json JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # 3. Create resumes table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id UUID PRIMARY KEY,
                candidate_name TEXT,
                email TEXT,
                phone TEXT,
                type TEXT NOT NULL,
                title TEXT,
                text TEXT,
                embedding vector(768),
                metadata JSONB,
                canonical_json JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # 4. Create candidate_outreach table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS candidate_outreach (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                resume_id UUID REFERENCES resumes(id),
                jd_id UUID REFERENCES memories(id),
                candidate_email VARCHAR(255) NOT NULL,
                candidate_name VARCHAR(255),
                email_subject TEXT,
                email_body TEXT,
                embedding vector(768),
                sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                acknowledgement VARCHAR(20),
                acknowledged_at TIMESTAMP WITH TIME ZONE,
                ats_score INTEGER,
                rank INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # 5. Create interview_schedules table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS interview_schedules (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                resume_id UUID REFERENCES resumes(id),
                jd_id UUID REFERENCES memories(id),
                outreach_id UUID REFERENCES candidate_outreach(id),
                interview_date DATE NOT NULL,
                proposed_slots JSONB,
                selected_slot VARCHAR(10),
                confirmed_slot_time TIMESTAMP WITH TIME ZONE,
                event_id VARCHAR(255),
                event_link TEXT,
                meet_link TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Indexes for candidate_outreach
        cur.execute("CREATE INDEX IF NOT EXISTS idx_candidate_outreach_resume ON candidate_outreach(resume_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_candidate_outreach_jd ON candidate_outreach(jd_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_candidate_outreach_email ON candidate_outreach(candidate_email);")

        # 6. Create meet_bot_logs table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS meet_bot_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                interview_id UUID REFERENCES interview_schedules(id),
                event_type TEXT NOT NULL,
                payload JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # 7. Create users table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # 8. Add short_id to memories if not exists
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='memories' AND column_name='short_id') THEN 
                    ALTER TABLE memories ADD COLUMN short_id VARCHAR(10);
                    CREATE INDEX idx_memories_short_id ON memories(short_id);
                END IF; 
            END $$;
        """)

        # 9. Add feedback columns to interview_schedules if not exists
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='interview_schedules' AND column_name='feedback_form_link') THEN 
                    ALTER TABLE interview_schedules ADD COLUMN feedback_form_link VARCHAR(500);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='interview_schedules' AND column_name='feedback_sent_at') THEN 
                    ALTER TABLE interview_schedules ADD COLUMN feedback_sent_at TIMESTAMP WITH TIME ZONE;
                END IF;
            END $$;
        """)


        # 10. Create feedback table for storing interview feedback from Google Sheets
        cur.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                timestamp TIMESTAMP WITH TIME ZONE,
                applicant_name VARCHAR(255),
                interview_date DATE,
                interviewer VARCHAR(255),
                interview_type VARCHAR(100),
                job_opening_id VARCHAR(50),
                technical_skills FLOAT,
                education_training FLOAT,
                work_experience FLOAT    ,
                organizational_skills FLOAT,
                communication FLOAT,
                attitude FLOAT,
                overall_rating FLOAT,
                final_recommendation VARCHAR(50),
                comments TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Create index on applicant_name and interview_date for faster queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_applicant ON feedback(applicant_name);
            CREATE INDEX IF NOT EXISTS idx_feedback_date ON feedback(interview_date);
        """)

        # 11. Alter columns to NUMERIC to support decimals (e.g. 4.5)
        # This is needed because the initial creation used INTEGER
        numeric_cols = [
            'technical_skills', 'education_training', 'work_experience', 
            'organizational_skills', 'communication', 'attitude', 'overall_rating'
        ]
        for col in numeric_cols:
            cur.execute(f"""
                DO $$ 
                BEGIN 
                    BEGIN
                        ALTER TABLE feedback ALTER COLUMN {col} TYPE NUMERIC(4, 1);
                    EXCEPTION
                        WHEN OTHERS THEN NULL;
                    END;
                END $$;
            """)

        # 12. Add interview_id to feedback table to link feedback with interviews
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='feedback' AND column_name='interview_id') THEN 
                    ALTER TABLE feedback ADD COLUMN interview_id UUID REFERENCES interview_schedules(id);
                    CREATE INDEX idx_feedback_interview_id ON feedback(interview_id);
                END IF;
            END $$;
        """)

        # 14. Add Technical Round decision and HR Round tracking columns
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='interview_schedules' AND column_name='technical_decision') THEN 
                    ALTER TABLE interview_schedules ADD COLUMN technical_decision VARCHAR(50);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='interview_schedules' AND column_name='technical_decision_sent_at') THEN 
                    ALTER TABLE interview_schedules ADD COLUMN technical_decision_sent_at TIMESTAMP WITH TIME ZONE;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='interview_schedules' AND column_name='hr_round_scheduled') THEN 
                    ALTER TABLE interview_schedules ADD COLUMN hr_round_scheduled BOOLEAN DEFAULT FALSE;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='interview_schedules' AND column_name='hr_interview_date') THEN 
                    ALTER TABLE interview_schedules ADD COLUMN hr_interview_date DATE;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='interview_schedules' AND column_name='hr_confirmed_slot_time') THEN 
                    ALTER TABLE interview_schedules ADD COLUMN hr_confirmed_slot_time TIMESTAMP WITH TIME ZONE;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='interview_schedules' AND column_name='hr_event_id') THEN 
                    ALTER TABLE interview_schedules ADD COLUMN hr_event_id VARCHAR(255);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='interview_schedules' AND column_name='hr_event_link') THEN 
                    ALTER TABLE interview_schedules ADD COLUMN hr_event_link TEXT;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='interview_schedules' AND column_name='hr_meet_link') THEN 
                    ALTER TABLE interview_schedules ADD COLUMN hr_meet_link TEXT;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='interview_schedules' AND column_name='hr_feedback_sent_at') THEN 
                    ALTER TABLE interview_schedules ADD COLUMN hr_feedback_sent_at TIMESTAMP WITH TIME ZONE;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='interview_schedules' AND column_name='hr_decision') THEN 
                    ALTER TABLE interview_schedules ADD COLUMN hr_decision VARCHAR(50);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='interview_schedules' AND column_name='hr_decision_sent_at') THEN 
                    ALTER TABLE interview_schedules ADD COLUMN hr_decision_sent_at TIMESTAMP WITH TIME ZONE;
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='interview_schedules' AND column_name='interview_round') THEN 
                    ALTER TABLE interview_schedules ADD COLUMN interview_round INTEGER DEFAULT 1;
                END IF;
            END $$;
        """)

        # 15. Create HR feedback table for comprehensive HR round feedback
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hr_feedback (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                interview_id UUID REFERENCES interview_schedules(id),
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                -- Candidate Information
                candidate_name VARCHAR(255),
                job_title VARCHAR(255),
                interview_date VARCHAR(100),
                interviewer_name VARCHAR(255),
                current_ctc VARCHAR(100),
                expected_ctc VARCHAR(100),
                company_ctc VARCHAR(100),
                reason_leave TEXT,
                notice_period VARCHAR(100),
                joining_date DATE,
                
                -- Skills & Competencies (1-5)
                technical_skills INTEGER,
                communication_skills INTEGER,
                problem_solving INTEGER,
                teamwork INTEGER,
                leadership INTEGER,
                domain_knowledge INTEGER,
                adaptability INTEGER,
                cultural_fit INTEGER,
                
                -- Behavioral Evaluation (1-5)
                confidence INTEGER,
                attitude INTEGER,
                time_management INTEGER,
                motivation INTEGER,
                integrity INTEGER,
                
                -- Interview Performance (1-5)
                clarity INTEGER,
                examples_quality INTEGER,
                job_understanding INTEGER,
                
                -- Overall Assessment
                strengths TEXT,
                improvements TEXT,
                concerns TEXT,
                
                -- Recommendation
                recommendation VARCHAR(100),
                additional_comments TEXT,
                
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        # Create index on interview_id for HR feedback
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_hr_feedback_interview_id ON hr_feedback(interview_id);
        """)

        conn.commit()

        # 16. Add user_id to memories and resumes for tracking uploader
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='memories' AND column_name='user_id') THEN 
                    ALTER TABLE memories ADD COLUMN user_id UUID REFERENCES users(id);
                END IF;
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='resumes' AND column_name='user_id') THEN 
                    ALTER TABLE resumes ADD COLUMN user_id UUID REFERENCES users(id);
                END IF;
            END $$;
        """)

        conn.commit()

        # 17. Add role column to users table if not exists
        cur.execute("""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='role') THEN 
                    ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'recruiter';
                END IF;
            END $$;
        """)

        conn.commit()
        cur.close()
        print("Database initialized successfully.")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
