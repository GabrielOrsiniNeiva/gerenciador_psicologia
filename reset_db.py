import os
from gerenciador_psicologia.app import app, db

def reset_database():
    """Drops and recreates all database tables."""
    with app.app_context():
        database_url = os.environ.get("DATABASE_URL")
        print(f"DATABASE_URL is: {database_url}")
        print("Dropping all database tables...")
        db.drop_all()
        print("Creating all database tables...")
        db.create_all()
        print("Database has been reset successfully.")

if __name__ == "__main__":
    reset_database()
