"""
Migration: Add execution_time_ms column to audit_logs table
"""
from sqlalchemy import create_engine, text
from config import DATABASE_URL

def upgrade():
    """Add missing columns to audit_logs table"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Add execution_time_ms
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='audit_logs' AND column_name='execution_time_ms'
        """))
        
        if not result.fetchone():
            print("Adding execution_time_ms column...")
            conn.execute(text("ALTER TABLE audit_logs ADD COLUMN execution_time_ms INTEGER"))
            conn.commit()
            print("✓ execution_time_ms added")
        else:
            print("✓ execution_time_ms exists")
        
        # Add fallback_used
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='audit_logs' AND column_name='fallback_used'
        """))
        
        if not result.fetchone():
            print("Adding fallback_used column...")
            conn.execute(text("ALTER TABLE audit_logs ADD COLUMN fallback_used VARCHAR(10) DEFAULT 'false'"))
            conn.commit()
            print("✓ fallback_used added")
        else:
            print("✓ fallback_used exists")
        
        # Add retry_count
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='audit_logs' AND column_name='retry_count'
        """))
        
        if not result.fetchone():
            print("Adding retry_count column...")
            conn.execute(text("ALTER TABLE audit_logs ADD COLUMN retry_count INTEGER DEFAULT 0"))
            conn.commit()
            print("✓ retry_count added")
        else:
            print("✓ retry_count exists")

def downgrade():
    """Remove added columns"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execute(text("""
            ALTER TABLE audit_logs 
            DROP COLUMN IF EXISTS execution_time_ms,
            DROP COLUMN IF EXISTS fallback_used,
            DROP COLUMN IF EXISTS retry_count
        """))
        conn.commit()
        print("✓ Columns removed")

if __name__ == "__main__":
    print("Running migration: add_execution_time_ms")
    upgrade()
    print("Migration completed!")
