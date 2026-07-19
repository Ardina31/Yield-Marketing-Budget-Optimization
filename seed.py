"""
Populates the database with a demo admin account and a realistic, sizeable
campaign history (30 campaigns x up to 6 months each, across 8 channels),
so the dashboard, pagination, charts, and optimizer all have something
substantial to show immediately.

    $ python seed.py
"""
import random

from app import create_app
from app.extensions import db
from app.models import Campaign, CampaignMetric, Channel, Setting, User
from app.models.channel import DEFAULT_CHANNELS

app = create_app()

ADMIN_EMAIL = "admin@yield.app"
ADMIN_PASSWORD = "admin123"

# (channel name, base click-through rate, base revenue multiplier)
CHANNEL_PROFILES = [
    ("Google Ads", 0.028, 1.4),
    ("Meta Ads", 0.019, 1.1),
    ("Instagram", 0.022, 0.95),
    ("TikTok Ads", 0.031, 0.85),
    ("LinkedIn Ads", 0.012, 1.6),
    ("YouTube Ads", 0.017, 1.2),
    ("Email", 0.065, 3.8),
    ("Affiliate", 0.045, 2.1),
]

CAMPAIGN_THEMES = [
    "Spring Refresh", "Summer Sale", "Back to School", "Fall Launch", "Holiday Gift Guide",
    "New Year Reset", "Flash Deal", "VIP Early Access", "Clearance Blowout", "Product Launch",
    "Loyalty Rewards", "Cart Recovery", "Win-Back", "Referral Push", "Brand Awareness",
    "Category Spotlight", "Bundle Promo", "Free Shipping Weekend", "Anniversary Sale",
    "Influencer Collab", "UGC Campaign", "Retargeting Wave", "Lookalike Expansion",
    "Geo Test — West", "Geo Test — East", "Mobile App Install", "Webinar Signup",
    "Trial Extension", "Upsell Sequence", "Cross-Sell Bundle",
]

PERIODS = [
    "2025-10", "2025-11", "2025-12", "2026-01", "2026-02",
    "2026-03", "2026-04", "2026-05", "2026-06", "2026-07",
]


def seed():
    with app.app_context():
        db.create_all()

        if Channel.query.count() == 0:
            for c in DEFAULT_CHANNELS:
                db.session.add(Channel(**c))
            db.session.commit()
            print("Seeded default channels.")

        admin = User.query.filter_by(email=ADMIN_EMAIL).first()
        if not admin:
            admin = User(name="Alex Morgan", email=ADMIN_EMAIL, role="admin", company_name="Yield Demo Co.")
            admin.set_password(ADMIN_PASSWORD)
            db.session.add(admin)
            db.session.flush()
            db.session.add(Setting(user_id=admin.id))
            db.session.commit()
            print(f"Created admin user ({ADMIN_EMAIL} / {ADMIN_PASSWORD}).")
        else:
            print("Admin user already exists — skipping user creation.")

        if Campaign.query.filter_by(user_id=admin.id).count() > 0:
            print("Campaign data already present — skipping data seed.")
            return

        random.seed(7)
        channel_cache = {name: Channel.query.filter_by(name=name).first() for name, _, _ in CHANNEL_PROFILES}

        metric_rows_written = 0
        for i, theme in enumerate(CAMPAIGN_THEMES, start=1):
            channel_name, base_ctr, base_roi_mult = random.choice(CHANNEL_PROFILES)
            channel = channel_cache[channel_name]

            n_periods = random.randint(2, 6)
            chosen_periods = sorted(random.sample(PERIODS, n_periods))
            base_cost = random.uniform(400, 9500)

            campaign = Campaign(
                name=f"{theme} #{i}",
                channel_id=channel.id,
                user_id=admin.id,
                objective=random.choice(["awareness", "traffic", "conversions", "retention"]),
                budget_allocated=round(base_cost, 2),
                status="active",
            )
            db.session.add(campaign)
            db.session.flush()

            for period in chosen_periods:
                drift = random.uniform(0.75, 1.35)
                cost = round(base_cost * drift, 2)
                impressions = int(cost * random.uniform(14, 34))
                ctr = base_ctr * random.uniform(0.7, 1.3)
                clicks = max(1, int(impressions * ctr))
                conv_rate = random.uniform(0.01, 0.09)
                conversions = max(0, int(clicks * conv_rate))
                roi_mult = base_roi_mult * random.uniform(0.55, 1.5)
                revenue = round(cost * roi_mult, 2)

                db.session.add(CampaignMetric(
                    campaign_id=campaign.id,
                    period=period,
                    cost=cost,
                    revenue=revenue,
                    impressions=impressions,
                    clicks=clicks,
                    conversions=conversions,
                ))
                metric_rows_written += 1

        db.session.commit()
        print(
            f"Seeded {len(CAMPAIGN_THEMES)} campaigns "
            f"({metric_rows_written} monthly metric rows) across {len(PERIODS)} periods."
        )


if __name__ == "__main__":
    seed()
