"""Additive schema upgrades preserve existing pantry and exchange records."""

from sqlalchemy.orm import Session
from .models import Base, SchemaVersion, GeneratedRecipe, GenerationBudget


def migrate(engine):
    Base.metadata.create_all(engine)
    with Session(engine) as db, db.begin():
        if not db.get(SchemaVersion, 1):
            db.add(SchemaVersion(version=1))
        if not db.get(SchemaVersion, 2):
            GeneratedRecipe.__table__.create(engine, checkfirst=True)
            GenerationBudget.__table__.create(engine, checkfirst=True)
            db.add(SchemaVersion(version=2))
