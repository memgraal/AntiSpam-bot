import os
from sqlalchemy import (
    Column, create_engine, Boolean, BigInteger,
    ForeignKey, Integer, String
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from config import DB_PATH, DB_URL

Base = declarative_base()


# ============================================================
#                       GROUP MODEL
# ============================================================
class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, unique=True, nullable=False)

    # Relationships
    users = relationship(
        "ChatUser",
        back_populates="group",
        cascade="all, delete"
    )
    settings = relationship(
        "GroupSettings",
        back_populates="group",
        uselist=False,
        cascade="all, delete-orphan"
    )
    badwords = relationship(
        "BadWord",
        back_populates="group",
        cascade="all, delete-orphan"
    )


# ============================================================
#                     BAD WORD MODEL
# ============================================================
class BadWord(Base):
    __tablename__ = "bad_words"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    word = Column(String, nullable=False)

    group = relationship("Group", back_populates="badwords")

    def __repr__(self):
        return f"<BadWord(group_id={self.group_id}, word='{self.word}')>"


# ============================================================
#                     CHAT USER MODEL
# ============================================================
class ChatUser(Base):
    __tablename__ = "chat_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)

    is_verified = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    is_captcha_sent = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    group = relationship("Group", back_populates="users")

    @staticmethod
    def is_user_banned(session, username: str) -> bool:
        return session.query(ChatUser).filter_by(username=username, is_banned=True).first() is not None

    @staticmethod
    def is_user_verified(session, username: str) -> bool:
        return session.query(ChatUser).filter_by(username=username, is_verified=True).first() is not None

    @staticmethod
    def is_user_admin(session, username: str) -> bool:
        return session.query(ChatUser).filter_by(username=username, is_admin=True).first() is not None

    def __repr__(self):
        return f'<ChatUser(username="{self.username}", admin={self.is_admin})>'


# ============================================================
#                   GROUP SETTINGS MODEL
# ============================================================
class GroupSettings(Base):
    __tablename__ = "group_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), unique=True, nullable=False)

    filter_badwords = Column(Boolean, default=True)
    welcome_enabled = Column(Boolean, default=True)
    ai_filtering = Column(Boolean, default=True)

    group = relationship("Group", back_populates="settings")

    def __repr__(self):
        return f"<GroupSettings(group_id={self.group_id})>"


# ============================================================
#                        ENGINE + SESSION
# ============================================================
engine = create_engine(DB_URL, echo=False)
Session = sessionmaker(bind=engine)

# Create tables only if DB does not exist
if not os.path.exists(DB_PATH):
    Base.metadata.create_all(engine)
