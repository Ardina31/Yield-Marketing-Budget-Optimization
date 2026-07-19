from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import DecimalField, SelectField, StringField
from wtforms.validators import DataRequired, Length, NumberRange

from app.models.campaign import CampaignObjective, CampaignStatus


class CampaignForm(FlaskForm):
    name = StringField("Campaign name", validators=[DataRequired(), Length(max=160)])
    channel_id = SelectField("Channel", coerce=int, validators=[DataRequired()])
    objective = SelectField(
        "Objective",
        choices=[(o, o.title()) for o in CampaignObjective.ALL],
        default=CampaignObjective.CONVERSIONS,
    )
    status = SelectField(
        "Status",
        choices=[(s, s.title()) for s in CampaignStatus.ALL],
        default=CampaignStatus.ACTIVE,
    )
    budget_allocated = DecimalField(
        "Planned budget ($)", validators=[DataRequired(), NumberRange(min=0)], places=2
    )


class UploadForm(FlaskForm):
    file = FileField(
        "Campaign data file",
        validators=[FileRequired(), FileAllowed(["csv", "xlsx", "xls"], "CSV or Excel files only.")],
    )
    period = StringField(
        "Reporting period (e.g. January or 2026-01)", validators=[DataRequired(), Length(max=20)]
    )
