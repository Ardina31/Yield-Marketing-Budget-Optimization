from datetime import datetime, timezone

from app.extensions import db


class ReportType:
    PDF = "pdf"
    EXCEL = "xlsx"
    CSV = "csv"
    ALL = (PDF, EXCEL, CSV)


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title = db.Column(db.String(160), nullable=False)
    report_type = db.Column(db.String(10), nullable=False, default=ReportType.PDF)
    file_path = db.Column(db.String(255), nullable=False)
    file_size_bytes = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Report {self.title!r} ({self.report_type})>"
