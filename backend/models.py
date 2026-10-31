from sqlalchemy import Column, Integer, Float, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SchemaVersion(Base):
    __tablename__ = "schema_version"
    version = Column(Integer, primary_key=True)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    color = Column(String, nullable=False)
    servings = Column(Integer, default=2, nullable=False)
    diet = Column(String, default="All", nullable=False)
    max_minutes = Column(Integer, default=60, nullable=False)


class SessionToken(Base):
    __tablename__ = "sessions"
    token_hash = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(Float, nullable=False)


class PantryItem(Base):
    __tablename__ = "pantry"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    stored_on = Column(String, nullable=False)
    location = Column(String, nullable=False)


class Community(Base):
    __tablename__ = "communities"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    invite_code = Column(String, unique=True, nullable=False)
    color = Column(String, nullable=False)


class Membership(Base):
    __tablename__ = "memberships"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "community_id"),)


class Friend(Base):
    __tablename__ = "friends"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    friend_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "friend_id"),)


class FriendInvite(Base):
    __tablename__ = "friend_invites"
    code = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(Float, nullable=False)


class IngredientRequest(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    community_id = Column(Integer, ForeignKey("communities.id"))
    friend_id = Column(Integer, ForeignKey("users.id"))
    provider_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    recipe_id = Column(String)
    note = Column(String, default="", nullable=False)
    deadline = Column(Float, nullable=False)
    status = Column(String, default="pending", nullable=False)
    created_at = Column(Float, nullable=False)
    completed_at = Column(Float)
    # Reserved pantry batches are returned on cancellation, preserving their original storage dates.
    reserved = Column(String, default="[]", nullable=False)


class Decline(Base):
    __tablename__ = "declines"
    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    __table_args__ = (UniqueConstraint("request_id", "user_id"),)


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    community_id = Column(Integer, ForeignKey("communities.id"))
    request_id = Column(Integer, ForeignKey("requests.id"))
    body = Column(String, nullable=False)
    created_at = Column(Float, nullable=False)


class Cook(Base):
    __tablename__ = "cooks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipe_id = Column(String, nullable=False)
    request_key = Column(String, nullable=False)
    created_at = Column(Float, nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "request_key"),)


class PantryImport(Base):
    __tablename__ = "pantry_imports"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    request_key = Column(String, nullable=False)
    __table_args__ = (UniqueConstraint("user_id", "request_key"),)


class GeneratedRecipe(Base):
    __tablename__ = "generated_recipes"
    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    context_hash = Column(String, nullable=False)
    payload = Column(String, nullable=False)
    created_at = Column(Float, nullable=False)


class GenerationBudget(Base):
    __tablename__ = "generation_budgets"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    last_attempt = Column(Float, nullable=False)
    busy_until = Column(Float, nullable=False, default=0)
