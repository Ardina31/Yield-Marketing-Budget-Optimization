from app.extensions import db


class Channel(db.Model):
    """A marketing channel / platform, e.g. Google Ads, Meta Ads, Email."""

    __tablename__ = "channels"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, default="other")
    color_hex = db.Column(db.String(7), nullable=False, default="#0F766E")
    icon = db.Column(db.String(40), nullable=False, default="megaphone")

    campaigns = db.relationship("Campaign", backref="channel", lazy="dynamic")

    def __repr__(self):
        return f"<Channel {self.name!r}>"


# Canonical seed list used by the import service to auto-create channels
# the first time they are encountered in an uploaded file.
DEFAULT_CHANNELS = [
    {"name": "Google Ads", "category": "paid_search", "color_hex": "#4285F4", "icon": "search"},
    {"name": "Meta Ads", "category": "paid_social", "color_hex": "#0866FF", "icon": "share-2"},
    {"name": "Instagram", "category": "paid_social", "color_hex": "#E1306C", "icon": "instagram"},
    {"name": "TikTok Ads", "category": "paid_social", "color_hex": "#000000", "icon": "music"},
    {"name": "LinkedIn Ads", "category": "paid_social", "color_hex": "#0A66C2", "icon": "linkedin"},
    {"name": "Email", "category": "owned", "color_hex": "#0F766E", "icon": "mail"},
    {"name": "Affiliate", "category": "partnership", "color_hex": "#B45309", "icon": "link"},
    {"name": "YouTube Ads", "category": "video", "color_hex": "#FF0000", "icon": "youtube"},
    {"name": "Other", "category": "other", "color_hex": "#64748B", "icon": "layers"},
]
