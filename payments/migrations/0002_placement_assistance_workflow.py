from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(
            settings.AUTH_USER_MODEL
        ),
        (
            "internships",
            "0006_applicationmessage_deleted_for_employer_and_more",
        ),
        (
            "payments",
            "0001_initial",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="placementassistancerequest",
            name="institution_notes",
            field=models.TextField(
                blank=True,
                default="",
            ),
        ),
        migrations.AddField(
            model_name="placementassistancerequest",
            name="managed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name=(
                    "placement_assistance_requests_managed"
                ),
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="placementassistancerequest",
            name="matched_opportunity",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name=(
                    "placement_assistance_matches"
                ),
                to="internships.internshipopportunity",
            ),
        ),
        migrations.AddField(
            model_name="placementassistancerequest",
            name="matching_started_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="placementassistancerequest",
            name="placed_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="placementassistancerequest",
            name="shortlisted_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="placementassistancerequest",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    (
                        "awaiting_verification",
                        "Awaiting Verification",
                    ),
                    (
                        "awaiting_payment",
                        "Awaiting Payment",
                    ),
                    ("active", "Active"),
                    (
                        "matching",
                        "Matching in Progress",
                    ),
                    (
                        "shortlisted",
                        "Opportunity Shortlisted",
                    ),
                    ("placed", "Placement Found"),
                    ("cancelled", "Cancelled"),
                ],
                db_index=True,
                default="draft",
                max_length=30,
            ),
        ),
    ]
