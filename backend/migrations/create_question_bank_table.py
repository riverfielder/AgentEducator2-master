from sqlalchemy import create_engine, text, inspect
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import Config
db_uri = Config.SQLALCHEMY_DATABASE_URI

def check_table_exists(connection, table_name):
    inspector = inspect(connection)
    return table_name in inspector.get_table_names()

def create_table():
    engine = create_engine(db_uri)
    with engine.connect() as connection:
        if not check_table_exists(connection, 'question_bank'):
            print("Creating question_bank table...")
            create_table_sql = '''
            CREATE TABLE IF NOT EXISTS question_bank (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                question_type VARCHAR(16) NOT NULL,
                options JSON,
                answer JSON NOT NULL,
                explanation TEXT,
                creator_id INTEGER NOT NULL,
                created_at DATETIME,
                category VARCHAR(64),
                difficulty VARCHAR(16),
                tags JSON,
                remark TEXT
            );
            '''
            connection.execute(text(create_table_sql))
            print("question_bank table created.")
        else:
            print("question_bank table already exists.")
        connection.commit()

def drop_table():
    engine = create_engine(db_uri)
    with engine.connect() as connection:
        if check_table_exists(connection, 'question_bank'):
            print("Dropping question_bank table...")
            connection.execute(text("DROP TABLE question_bank;"))
            print("question_bank table dropped.")
        else:
            print("question_bank table does not exist.")
        connection.commit()

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--drop':
        drop_table()
    else:
        create_table() 