from app.extensions import db
from app.models import Campaign, Channel


def list_campaigns(user_id: int, search: str = "", channel_id: int | None = None,
                    status: str | None = None, sort: str = "recent"):
    query = Campaign.query.filter_by(user_id=user_id)

    if search:
        query = query.filter(Campaign.name.ilike(f"%{search}%"))
    if channel_id:
        query = query.filter(Campaign.channel_id == channel_id)
    if status and status != "all":
        query = query.filter(Campaign.status == status)

    if sort == "name":
        query = query.order_by(Campaign.name.asc())
    elif sort == "budget":
        query = query.order_by(Campaign.budget_allocated.desc())
    else:
        query = query.order_by(Campaign.created_at.desc())

    return query


def get_campaign_or_404(campaign_id: int, user_id: int) -> Campaign:
    return Campaign.query.filter_by(id=campaign_id, user_id=user_id).first_or_404()


def create_campaign(user_id: int, name: str, channel_id: int, objective: str,
                     budget_allocated: float, status: str = "active") -> Campaign:
    campaign = Campaign(
        name=name,
        channel_id=channel_id,
        objective=objective,
        budget_allocated=budget_allocated,
        status=status,
        user_id=user_id,
    )
    db.session.add(campaign)
    db.session.commit()
    return campaign


def update_campaign(campaign: Campaign, **fields) -> Campaign:
    for key, value in fields.items():
        if value is not None and hasattr(campaign, key):
            setattr(campaign, key, value)
    db.session.commit()
    return campaign


def delete_campaign(campaign: Campaign) -> None:
    db.session.delete(campaign)
    db.session.commit()


def all_channels():
    return Channel.query.order_by(Channel.name.asc()).all()
