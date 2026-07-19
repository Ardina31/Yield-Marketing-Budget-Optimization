from datetime import datetime

from flask import Blueprint, render_template, request, send_file
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Report
from app.models.report import ReportType
from app.services.activity_service import log_activity
from app.services.analytics_service import compute_kpis, get_available_periods, get_campaign_rows
from app.services.report_service import generate_csv_report, generate_excel_report, generate_pdf_report

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@login_required
def index():
    periods = get_available_periods(current_user.id)
    history = (
        Report.query.filter_by(user_id=current_user.id)
        .order_by(Report.created_at.desc())
        .limit(20)
        .all()
    )
    return render_template("reports/index.html", periods=periods, history=history)


def _save_report_record(report_type: str, filename: str, size_bytes: int) -> None:
    report = Report(
        user_id=current_user.id,
        title=filename,
        report_type=report_type,
        file_path=filename,
        file_size_bytes=size_bytes,
    )
    db.session.add(report)
    db.session.commit()


@reports_bp.route("/export/pdf")
@login_required
def export_pdf():
    period = request.args.get("period", "All")
    rows = get_campaign_rows(current_user.id, period=period)
    kpis = compute_kpis(rows)

    buf = generate_pdf_report(current_user.name, kpis, rows)
    filename = f"Yield_Report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"

    _persist_and_log(buf, filename, ReportType.PDF)
    return send_file(buf, as_attachment=True, download_name=filename, mimetype="application/pdf")


@reports_bp.route("/export/excel")
@login_required
def export_excel():
    period = request.args.get("period", "All")
    rows = get_campaign_rows(current_user.id, period=period)
    kpis = compute_kpis(rows)

    buf = generate_excel_report(kpis, rows)
    filename = f"Yield_Report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"

    _persist_and_log(buf, filename, ReportType.EXCEL)
    return send_file(
        buf, as_attachment=True, download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@reports_bp.route("/export/csv")
@login_required
def export_csv():
    period = request.args.get("period", "All")
    rows = get_campaign_rows(current_user.id, period=period)

    buf = generate_csv_report(rows)
    filename = f"Yield_Report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    log_activity(current_user.id, "report_export", f"Exported CSV report ({filename}).")
    _save_report_record(ReportType.CSV, filename, len(buf.getvalue()))

    return send_file(
        _string_io_to_bytes(buf), as_attachment=True, download_name=filename, mimetype="text/csv"
    )


def _persist_and_log(buf, filename, report_type):
    size = len(buf.getvalue())
    log_activity(current_user.id, "report_export", f"Exported {report_type.upper()} report ({filename}).")
    _save_report_record(report_type, filename, size)
    buf.seek(0)


def _string_io_to_bytes(string_buf):
    import io
    data = string_buf.getvalue().encode("utf-8")
    return io.BytesIO(data)
