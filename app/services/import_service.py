"""Parses uploaded CSV/Excel campaign data and writes it into the normalized
Campaign / CampaignMetric tables, auto-creating channels as needed."""
import io

import pandas as pd

from app.extensions import db
from app.models import Campaign, CampaignMetric, Channel
from app.utils.constants import CSV_COLUMN_ALIASES, REQUIRED_IMPORT_COLUMNS


class ImportError_(Exception):
    """Raised for any recoverable data-import problem (shown to the user)."""


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    df.rename(columns={k: v for k, v in CSV_COLUMN_ALIASES.items() if k in df.columns}, inplace=True)
    return df


def _get_or_create_channel(name: str) -> Channel:
    name = (name or "Other").strip() or "Other"
    channel = Channel.query.filter(db.func.lower(Channel.name) == name.lower()).first()
    if channel:
        return channel
    channel = Channel(name=name, category="other", color_hex="#64748B", icon="layers")
    db.session.add(channel)
    db.session.flush()
    return channel


def parse_upload(file_storage) -> pd.DataFrame:
    """Read an uploaded CSV/XLSX FileStorage into a normalized DataFrame."""
    filename = (file_storage.filename or "").lower()

    if filename.endswith(".csv"):
        raw = file_storage.stream.read().decode("utf-8-sig", errors="replace")
        df = pd.read_csv(io.StringIO(raw))
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_storage)
    else:
        raise ImportError_("Unsupported file type. Please upload a .csv or .xlsx file.")

    df = _normalize_columns(df)

    missing = [c for c in REQUIRED_IMPORT_COLUMNS if c not in df.columns]
    if missing:
        raise ImportError_(
            "Your file is missing required column(s): "
            f"{', '.join(missing)}. Found columns: {', '.join(df.columns)}."
        )

    for optional in ("impressions", "clicks", "conversions"):
        if optional not in df.columns:
            df[optional] = 0
    if "period" not in df.columns:
        df["period"] = None

    df["cost"] = pd.to_numeric(df["cost"], errors="coerce").fillna(0.0)
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(0.0)
    df["impressions"] = pd.to_numeric(df["impressions"], errors="coerce").fillna(0).astype(int)
    df["clicks"] = pd.to_numeric(df["clicks"], errors="coerce").fillna(0).astype(int)
    df["conversions"] = pd.to_numeric(df["conversions"], errors="coerce").fillna(0).astype(int)

    if df.empty:
        raise ImportError_("The uploaded file has no data rows.")

    return df


def commit_dataframe(df: pd.DataFrame, user_id: int, default_period: str) -> dict:
    """Persist a parsed DataFrame as Campaign + CampaignMetric rows.

    Campaigns are matched by (user, name, channel); a new campaign is
    created if one doesn't already exist. Metrics are upserted per period.
    """
    created_campaigns = 0
    updated_campaigns = 0
    metric_rows_written = 0

    for _, row in df.iterrows():
        name = str(row["campaign_name"]).strip() or "Untitled Campaign"
        channel = _get_or_create_channel(str(row["channel"]))
        period = str(row["period"]).strip() if row.get("period") not in (None, "", "nan") else default_period
        period = period or default_period

        campaign = Campaign.query.filter_by(
            user_id=user_id, name=name, channel_id=channel.id
        ).first()

        if not campaign:
            campaign = Campaign(
                name=name,
                channel_id=channel.id,
                user_id=user_id,
                budget_allocated=float(row["cost"]),
            )
            db.session.add(campaign)
            db.session.flush()
            created_campaigns += 1
        else:
            updated_campaigns += 1

        metric = CampaignMetric.query.filter_by(campaign_id=campaign.id, period=period).first()
        if metric:
            metric.cost = float(row["cost"])
            metric.revenue = float(row["revenue"])
            metric.impressions = int(row["impressions"])
            metric.clicks = int(row["clicks"])
            metric.conversions = int(row["conversions"])
        else:
            metric = CampaignMetric(
                campaign_id=campaign.id,
                period=period,
                cost=float(row["cost"]),
                revenue=float(row["revenue"]),
                impressions=int(row["impressions"]),
                clicks=int(row["clicks"]),
                conversions=int(row["conversions"]),
            )
            db.session.add(metric)
        metric_rows_written += 1

    db.session.commit()
    return {
        "created_campaigns": created_campaigns,
        "updated_campaigns": updated_campaigns,
        "metric_rows_written": metric_rows_written,
    }
