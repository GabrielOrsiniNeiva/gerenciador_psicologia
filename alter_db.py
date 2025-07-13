from gerenciador_psicologia.app import app, db

def add_is_active_column():
    """Adds the is_active column to the patient table."""
    with app.app_context():
        with db.engine.connect() as con:
            try:
                con.execute(text('ALTER TABLE patient ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE'))
                print("Column 'is_active' added to 'patient' table successfully.")
            except Exception as e:
                if "column \"is_active\" of relation \"patient\" already exists" in str(e):
                    print("Column 'is_active' already exists in 'patient' table.")
                else:
                    raise e

if __name__ == "__main__":
    from sqlalchemy import text
    add_is_active_column()
