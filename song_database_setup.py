from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base

# Define the database file
DATABASE_URL = "sqlite:///songs.db"

# Create the engine
engine = create_engine(DATABASE_URL, echo=True)

# Create a base class for declarative models
Base = declarative_base()

class Song(Base):
    __tablename__ = 'songs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    song_title = Column(String, nullable=False)

    def __repr__(self):
        return f"<Song(id={self.id}, user_id={self.user_id}, song_title='{self.song_title}')>"

# Create the table in the database
if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Database 'songs.db' created successfully with table 'songs'.")
