"""Constants shared across the application (kept out of routes/services)."""

# Column names the CSV/Excel importer will accept and normalize.
CSV_COLUMN_ALIASES = {
    "campaign": "campaign_name",
    "campaign name": "campaign_name",
    "ad name": "campaign_name",
    "channel": "channel",
    "platform": "channel",
    "source": "channel",
    "network": "channel",
    "cost": "cost",
    "spend": "cost",
    "amount spent": "cost",
    "ad spend": "cost",
    "revenue": "revenue",
    "sales": "revenue",
    "value": "revenue",
    "return": "revenue",
    "impressions": "impressions",
    "clicks": "clicks",
    "conversions": "conversions",
    "month": "period",
    "period": "period",
}

REQUIRED_IMPORT_COLUMNS = ("campaign_name", "channel", "cost", "revenue")

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

TOAST_TYPES = ("info", "success", "warning", "danger")

NOTIFICATION_ICON_BY_TYPE = {
    "info": "info",
    "success": "check-circle",
    "warning": "alert-triangle",
    "danger": "alert-octagon",
}
