"""
Seeds demo data for local development and presentations.

Two datasets are available:

1. DEFAULT — the main admin account (admin@yield.app), seeded with a large,
   randomized 30-campaign / ~117-row dataset across 8 channels and 10
   months. This is the realistic, "real app under real load" demo: it
   exercises pagination, multi-period trends, and the optimizer at scale.

       $ python seed.py

2. STORY MODE (optional, additive) — a second account (demo@yield.app)
   seeded with a small, deliberately hand-crafted 6-campaign dataset where
   the winners and losers are obvious at a glance (Email is a clear
   standout, Instagram is deliberately losing money, etc). This is the
   "explain the product to someone in 30 seconds" demo — smaller and
   narrated, not realistic in volume.

       $ python seed.py --story

Both can be seeded in the same run; they live on separate accounts and
never touch each other's data.
"""
import argparse
import random

from app import create_app
from app.extensions import db
from app.models import Campaign, CampaignMetric, Channel, Setting, User
from app.models.channel import DEFAULT_CHANNELS

# ============================================================================
# Dataset 1 — default admin account: large, randomized, realistic scale
# ============================================================================
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


def ensure_channels():
    if Channel.query.count() == 0:
        for c in DEFAULT_CHANNELS:
            db.session.add(Channel(**c))
        db.session.commit()
        print("Seeded default channels.")


def ensure_user(email, password, name, company):
    user = User.query.filter_by(email=email).first()
    if user:
        print(f"User {email} already exists — skipping user creation.")
        return user, False
    user = User(name=name, email=email, role="admin", company_name=company)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    db.session.add(Setting(user_id=user.id))
    db.session.commit()
    print(f"Created user ({email} / {password}).")
    return user, True


def seed(app):
    """Seed the main, realistic-scale demo account. Safe to call on every boot -
    it checks for existing data first and does nothing if it's already there."""
    with app.app_context():
        db.create_all()
        ensure_channels()

        admin, _ = ensure_user(ADMIN_EMAIL, ADMIN_PASSWORD, "Alex Morgan", "Yield Demo Co.")

        if Campaign.query.filter_by(user_id=admin.id).count() > 0:
            print("Admin campaign data already present — skipping data seed.")
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
            f"({metric_rows_written} monthly metric rows) across {len(PERIODS)} periods "
            f"for {ADMIN_EMAIL}."
        )


# ============================================================================
# Dataset 2 — "story mode" account: small, hand-crafted, obvious narrative
# ============================================================================
STORY_EMAIL = "demo@yield.app"
STORY_PASSWORD = "demo123"

STORY_PERIODS = ["2026-05", "2026-06", "2026-07"]

# (campaign name, channel name, objective, base_cost, roi_multiplier, conv_rate)
# roi_multiplier is deliberately spread out so the story is obvious at a glance:
#   Email          -> clear standout winner
#   Affiliate       -> strong winner
#   Google Ads      -> solid, reliable performer
#   YouTube Ads     -> break-even-ish, awareness play
#   Meta Ads        -> mediocre, barely profitable
#   Instagram       -> clear loser, losing money every month
STORY_BLUEPRINT = [
    ("Retargeting Newsletter", "Email", "retention", 900, 8.10, 0.075),
    ("Partner Affiliate Drive", "Affiliate", "conversions", 2100, 2.90, 0.041),
    ("Summer Sale Search", "Google Ads", "conversions", 5200, 2.35, 0.050),
    ("Product Launch Video", "YouTube Ads", "awareness", 4100, 1.05, 0.020),
    ("Brand Awareness Push", "Meta Ads", "awareness", 3600, 1.15, 0.018),
    ("Influencer Collab", "Instagram", "traffic", 2800, 0.62, 0.026),
]


def seed_story(app):
    """Seed the small, curated 'explain it in 30 seconds' demo account."""
    with app.app_context():
        db.create_all()
        ensure_channels()

        demo, _ = ensure_user(STORY_EMAIL, STORY_PASSWORD, "Jordan Lee", "Story Mode Demo")

        if Campaign.query.filter_by(user_id=demo.id).count() > 0:
            print("Story-mode campaign data already present — skipping data seed.")
            return

        random.seed(42)
        for name, channel_name, objective, base_cost, roi_mult, conv_rate in STORY_BLUEPRINT:
            channel = Channel.query.filter_by(name=channel_name).first()
            campaign = Campaign(
                name=name,
                channel_id=channel.id,
                user_id=demo.id,
                objective=objective,
                budget_allocated=base_cost,
                status="active",
            )
            db.session.add(campaign)
            db.session.flush()

            for i, period in enumerate(STORY_PERIODS):
                growth = 1 + (i * 0.08) + random.uniform(-0.05, 0.05)
                cost = round(base_cost * growth, 2)
                revenue = round(cost * roi_mult * random.uniform(0.9, 1.1), 2)
                impressions = int(cost * random.uniform(18, 26))
                clicks = int(impressions * random.uniform(0.015, 0.045))
                conversions = max(1, int(clicks * conv_rate * random.uniform(0.85, 1.15)))

                db.session.add(CampaignMetric(
                    campaign_id=campaign.id,
                    period=period,
                    cost=cost,
                    revenue=revenue,
                    impressions=impressions,
                    clicks=clicks,
                    conversions=conversions,
                ))

        db.session.commit()
        print(
            f"Seeded {len(STORY_BLUEPRINT)} narrative campaigns across "
            f"{len(STORY_PERIODS)} periods for {STORY_EMAIL}."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Yield demo data.")
    parser.add_argument(
        "--story", action="store_true",
        help="Also seed a small, curated narrative demo account (demo@yield.app) for presentations.",
    )
    parser.add_argument(
        "--story-only", action="store_true",
        help="Seed only the narrative demo account, skipping the large admin dataset.",
    )
    args = parser.parse_args()

    app = create_app()

    if not args.story_only:
        seed(app)
    if args.story or args.story_only:
        seed_story(app)
