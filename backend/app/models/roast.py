import enum

from sqlalchemy import CheckConstraint, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class TipCategory(str, enum.Enum):
    structure = "structure"
    naming = "naming"
    bugs = "bugs"
    security = "security"
    readability = "readability"
    best_practices = "best_practices"


class Roast(Base):
    __tablename__ = "roasts"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(
        Integer, ForeignKey("submissions.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    roast_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    score = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    submission = relationship("Submission", back_populates="roast")
    tips = relationship("ImprovementTip", back_populates="roast", cascade="all, delete-orphan")

    __table_args__ = (CheckConstraint("score >= 0 AND score <= 100", name="ck_roasts_score_range"),)


class ImprovementTip(Base):
    __tablename__ = "improvement_tips"

    id = Column(Integer, primary_key=True, index=True)
    roast_id = Column(Integer, ForeignKey("roasts.id", ondelete="CASCADE"), nullable=False, index=True)
    category: Column[TipCategory] = Column(Enum(TipCategory, name="tip_category"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    file_path = Column(String(500), nullable=True)

    roast = relationship("Roast", back_populates="tips")
