from sqlalchemy import create_engine, text
from config.config import Config

db_uri = Config.SQLALCHEMY_DATABASE_URI

def alter_creator_id():
    engine = create_engine(db_uri)
    with engine.connect() as connection:
        print("Altering creator_id column type to VARCHAR(36)...")
        alter_sql = "ALTER TABLE question_bank MODIFY creator_id VARCHAR(36) NOT NULL;"
        connection.execute(text(alter_sql))
        print("Done.")
        connection.commit()

if __name__ == '__main__':
    alter_creator_id() 