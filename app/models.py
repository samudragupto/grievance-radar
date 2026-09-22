# SQLAlchemy models for Grievance Radar.

import json
from datetime import datetime

from app.database import db


class Complaint(db.Model):
    """Represents an ingested public complaint with metadata."""

    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=True)
    ward = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(100), nullable=True)
    filed_date = db.Column(db.Date, nullable=False)
    is_synthetic = db.Column(db.Boolean, default=True)
    embedded = db.Column(db.Boolean, default=False)
    cluster_id = db.Column(db.Integer, db.ForeignKey("clusters.id"), nullable=True)

    def to_dict(self):
        """Serialize complaint to dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "category": self.category,
            "ward": self.ward,
            "department": self.department,
            "filed_date": self.filed_date.isoformat() if self.filed_date else None,
            "is_synthetic": self.is_synthetic,
            "embedded": self.embedded,
            "cluster_id": self.cluster_id,
        }


class Cluster(db.Model):
    """Cluster of complaints identified via NLP embeddings."""

    __tablename__ = "clusters"

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(255), nullable=False)
    count = db.Column(db.Integer, default=0)
    ward = db.Column(db.String(50), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    avg_zscore = db.Column(db.Float, default=0.0)
    max_zscore = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    complaints = db.relationship("Complaint", backref="cluster", lazy=True)
    findings = db.relationship("Finding", backref="cluster", lazy=True)

    def to_dict(self):
        """Serialize cluster to dictionary."""
        return {
            "id": self.id,
            "label": self.label,
            "count": self.count,
            "ward": self.ward,
            "department": self.department,
            "avg_zscore": round(self.avg_zscore, 2),
            "max_zscore": round(self.max_zscore, 2),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Finding(db.Model):
    """Automated statistical spike finding flagged for human review."""

    __tablename__ = "findings"

    id = db.Column(db.Integer, primary_key=True)
    cluster_id = db.Column(db.Integer, db.ForeignKey("clusters.id"), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    z_score = db.Column(db.Float, nullable=False)
    percent_change = db.Column(db.Float, nullable=False)
    affected_count = db.Column(db.Integer, nullable=False)
    wards = db.Column(db.Text, nullable=False, default="[]")  # JSON string list
    suggested_dept = db.Column(db.String(100), nullable=False)
    sample_texts = db.Column(db.Text, nullable=False, default="[]")  # JSON string list
    status = db.Column(
        db.String(20), default="pending", nullable=False
    )  # pending, confirmed, dismissed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    decided_at = db.Column(db.DateTime, nullable=True)

    decisions = db.relationship("OfficerDecision", backref="finding", lazy=True)

    def get_wards(self):
        """Get parsed list of affected wards."""
        try:
            return json.loads(self.wards)
        except Exception:
            return [self.wards] if self.wards else []

    def get_sample_texts(self):
        """Get parsed sample texts."""
        try:
            return json.loads(self.sample_texts)
        except Exception:
            return []

    def to_dict(self):
        """Serialize finding to dictionary."""
        return {
            "id": self.id,
            "cluster_id": self.cluster_id,
            "title": self.title,
            "z_score": round(self.z_score, 2),
            "percent_change": round(self.percent_change, 1),
            "affected_count": self.affected_count,
            "wards": self.get_wards(),
            "suggested_dept": self.suggested_dept,
            "sample_texts": self.get_sample_texts(),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
        }


class Brief(db.Model):
    """Weekly summary brief generated from confirmed findings."""

    __tablename__ = "briefs"

    id = db.Column(db.Integer, primary_key=True)
    week_label = db.Column(db.String(50), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    findings = db.Column(db.Text, nullable=False, default="[]")  # JSON list of IDs
    pdf_path = db.Column(db.String(255), nullable=False)

    def get_finding_ids(self):
        """Get parsed list of finding IDs."""
        try:
            return json.loads(self.findings)
        except Exception:
            return []

    def to_dict(self):
        """Serialize brief to dictionary."""
        return {
            "id": self.id,
            "week_label": self.week_label,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "findings": self.get_finding_ids(),
            "pdf_path": self.pdf_path,
        }


class OfficerDecision(db.Model):
    """Audit log of human-in-the-loop decisions made by municipal officers."""

    __tablename__ = "officer_decisions"

    id = db.Column(db.Integer, primary_key=True)
    finding_id = db.Column(db.Integer, db.ForeignKey("findings.id"), nullable=False)
    action = db.Column(db.String(20), nullable=False)  # confirm | dismiss | edit
    edited_title = db.Column(db.String(255), nullable=True)
    edited_dept = db.Column(db.String(100), nullable=True)
    decided_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Serialize officer decision to dictionary."""
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "action": self.action,
            "edited_title": self.edited_title,
            "edited_dept": self.edited_dept,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
        }
