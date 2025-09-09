#!/usr/bin/env python3
"""
Database Migration Script for BigBossizzz Advanced Features
Run this script to add new tables and columns for enhanced security and functionality.
"""

from app import app, db
from models import UploadRecord, DeviceLog, SecurityAlert
from sqlalchemy import text
import logging

def run_migration():
    """Execute database migration for advanced features"""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    with app.app_context():
        try:
            logger.info("Starting database migration for advanced features...")
            
            # Create all new tables
            logger.info("Creating new tables...")
            db.create_all()
            
            # Add new columns to existing tables using raw SQL
            logger.info("Adding new columns to existing tables...")
            
            # Quiz table modifications
            quiz_columns = [
                "ALTER TABLE quiz ADD COLUMN allow_view_responses BOOLEAN DEFAULT 1",
                "ALTER TABLE quiz ADD COLUMN auto_generate_from_upload BOOLEAN DEFAULT 0", 
                "ALTER TABLE quiz ADD COLUMN draft_from_upload_id INTEGER",
                "ALTER TABLE quiz ADD COLUMN is_deleted BOOLEAN DEFAULT 0",
                "ALTER TABLE quiz ADD COLUMN max_violations_allowed INTEGER DEFAULT 3",
                "ALTER TABLE quiz ADD COLUMN auto_terminate_on_violation BOOLEAN DEFAULT 1",
                "ALTER TABLE quiz ADD COLUMN face_detection_required BOOLEAN DEFAULT 1",
                "ALTER TABLE quiz ADD COLUMN screen_recording_required BOOLEAN DEFAULT 0",
                "ALTER TABLE quiz ADD COLUMN browser_lockdown BOOLEAN DEFAULT 1"
            ]
            
            # QuizAttempt table modifications  
            attempt_columns = [
                "ALTER TABLE quiz_attempt ADD COLUMN report_sent BOOLEAN DEFAULT 0",
                "ALTER TABLE quiz_attempt ADD COLUMN violation_count INTEGER DEFAULT 0",
                "ALTER TABLE quiz_attempt ADD COLUMN is_flagged BOOLEAN DEFAULT 0",
                "ALTER TABLE quiz_attempt ADD COLUMN termination_reason TEXT"
            ]
            
            # Execute column additions (ignore errors if columns already exist)
            for sql in quiz_columns + attempt_columns:
                try:
                    db.session.execute(text(sql))
                    db.session.commit()
                    logger.info(f"Successfully executed: {sql}")
                except Exception as e:
                    db.session.rollback()
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        logger.info(f"Column already exists, skipping: {sql}")
                    else:
                        logger.warning(f"Error executing {sql}: {e}")
            
            # Create indexes for performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_upload_record_host ON upload_record(host_id)",
                "CREATE INDEX IF NOT EXISTS idx_device_log_user ON device_log(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_security_alert_user ON security_alert(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_quiz_attempt_quiz_user ON quiz_attempt(quiz_id, participant_id)",
                "CREATE INDEX IF NOT EXISTS idx_proctoring_event_attempt ON proctoring_event(attempt_id)"
            ]
            
            logger.info("Creating performance indexes...")
            for sql in indexes:
                try:
                    db.session.execute(text(sql))
                    db.session.commit()
                    logger.info(f"Created index: {sql}")
                except Exception as e:
                    db.session.rollback()
                    logger.info(f"Index already exists or error: {e}")
            
            logger.info("Database migration completed successfully!")
            
            # Verify tables exist
            logger.info("Verifying new tables...")
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            new_tables = ['upload_record', 'device_log', 'security_alert']
            
            for table in new_tables:
                if table in tables:
                    logger.info(f"✓ Table '{table}' created successfully")
                else:
                    logger.error(f"✗ Table '{table}' not found!")
            
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed. Check logs for details.")