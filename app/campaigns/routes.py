from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.campaigns.forms import CampaignForm, UploadForm
from app.models.user import Role
from app.services import campaign_service
from app.services.activity_service import log_activity
from app.services.import_service import ImportError_, commit_dataframe, parse_upload
from app.services.notification_service import notify
from app.utils.decorators import roles_required

campaigns_bp = Blueprint("campaigns", __name__, url_prefix="/campaigns")


@campaigns_bp.route("/")
@login_required
def list_view():
    search = request.args.get("q", "").strip()
    channel_id = request.args.get("channel", type=int)
    status = request.args.get("status", "all")
    sort = request.args.get("sort", "recent")
    page = request.args.get("page", 1, type=int)

    query = campaign_service.list_campaigns(
        current_user.id, search=search, channel_id=channel_id, status=status, sort=sort
    )
    pagination = query.paginate(page=page, per_page=10, error_out=False)

    return render_template(
        "campaigns/list.html",
        campaigns=pagination.items,
        pagination=pagination,
        channels=campaign_service.all_channels(),
        search=search,
        selected_channel=channel_id,
        selected_status=status,
        selected_sort=sort,
    )


@campaigns_bp.route("/<int:campaign_id>")
@login_required
def detail(campaign_id):
    campaign = campaign_service.get_campaign_or_404(campaign_id, current_user.id)
    metrics = campaign.metrics.order_by("period").all()
    totals = campaign.totals()
    return render_template("campaigns/detail.html", campaign=campaign, metrics=metrics, totals=totals)


@campaigns_bp.route("/new", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.AGENT)
def create():
    form = CampaignForm()
    form.channel_id.choices = [(c.id, c.name) for c in campaign_service.all_channels()]

    if form.validate_on_submit():
        campaign = campaign_service.create_campaign(
            user_id=current_user.id,
            name=form.name.data.strip(),
            channel_id=form.channel_id.data,
            objective=form.objective.data,
            budget_allocated=float(form.budget_allocated.data),
            status=form.status.data,
        )
        log_activity(current_user.id, "campaign_created", f"Created campaign '{campaign.name}'.")
        flash(f"Campaign '{campaign.name}' created.", "success")
        return redirect(url_for("campaigns.detail", campaign_id=campaign.id))

    return render_template("campaigns/form.html", form=form, mode="create")


@campaigns_bp.route("/<int:campaign_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.AGENT)
def edit(campaign_id):
    campaign = campaign_service.get_campaign_or_404(campaign_id, current_user.id)
    form = CampaignForm(obj=campaign)
    form.channel_id.choices = [(c.id, c.name) for c in campaign_service.all_channels()]

    if request.method == "GET":
        form.channel_id.data = campaign.channel_id

    if form.validate_on_submit():
        campaign_service.update_campaign(
            campaign,
            name=form.name.data.strip(),
            channel_id=form.channel_id.data,
            objective=form.objective.data,
            budget_allocated=float(form.budget_allocated.data),
            status=form.status.data,
        )
        flash(f"Campaign '{campaign.name}' updated.", "success")
        return redirect(url_for("campaigns.detail", campaign_id=campaign.id))

    return render_template("campaigns/form.html", form=form, mode="edit", campaign=campaign)


@campaigns_bp.route("/<int:campaign_id>/delete", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.AGENT)
def delete(campaign_id):
    campaign = campaign_service.get_campaign_or_404(campaign_id, current_user.id)
    name = campaign.name
    campaign_service.delete_campaign(campaign)
    log_activity(current_user.id, "campaign_deleted", f"Deleted campaign '{name}'.")
    flash(f"Campaign '{name}' deleted.", "info")
    return redirect(url_for("campaigns.list_view"))


@campaigns_bp.route("/upload", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.AGENT)
def upload():
    form = UploadForm()

    if form.validate_on_submit():
        try:
            df = parse_upload(form.file.data)
            default_period = form.period.data.strip() or datetime.utcnow().strftime("%Y-%m")
            summary = commit_dataframe(df, current_user.id, default_period)

            log_activity(
                current_user.id, "data_import",
                f"Imported {summary['metric_rows_written']} rows for period '{default_period}'.",
            )
            notify(
                current_user.id, "Data import complete",
                f"{summary['created_campaigns']} new campaign(s) and "
                f"{summary['updated_campaigns']} existing campaign(s) updated for {default_period}.",
                "success",
            )
            flash(
                f"Imported {summary['metric_rows_written']} rows "
                f"({summary['created_campaigns']} new campaigns).", "success",
            )
            return redirect(url_for("dashboard.index"))
        except ImportError_ as exc:
            flash(str(exc), "danger")
        except Exception as exc:  # unexpected parsing failure
            flash(f"We couldn't process that file: {exc}", "danger")

    return render_template("campaigns/upload.html", form=form)
