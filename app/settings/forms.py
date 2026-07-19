from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class ProfileForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    company_name = StringField("Company name", validators=[Length(max=120)])


class PreferencesForm(FlaskForm):
    currency = SelectField("Currency", choices=[("USD", "USD ($)"), ("EUR", "EUR (€)"), ("GBP", "GBP (£)"), ("INR", "INR (₹)")])
    timezone = StringField("Timezone", validators=[Length(max=60)])
    email_notifications = BooleanField("Email me about optimization results")
    default_optimization_goal = SelectField(
        "Default optimization goal",
        choices=[
            ("max_roi", "Maximize ROI"),
            ("max_conversions", "Maximize Conversions"),
            ("min_cost", "Minimize Cost"),
            ("balanced", "Balanced Strategy"),
        ],
    )


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField("Current password", validators=[DataRequired()])
    new_password = PasswordField("New password", validators=[DataRequired(), Length(min=8)])
    confirm_new_password = PasswordField(
        "Confirm new password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")],
    )
