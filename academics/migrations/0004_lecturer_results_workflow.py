from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        (
            "academics",
            "0003_gradescale_gradeband_semesterresultsubmission_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="academicstaffprofile",
            name="academic_role",
            field=models.CharField(
                choices=[
                    ("lecturer", "Lecturer"),
                    ("hod", "Head of Department"),
                    ("dean", "Dean"),
                ],
                max_length=10,
            ),
        ),
        migrations.CreateModel(
            name="LecturerUnitAssignment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "assigned_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="lecturer_unit_assignments_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "lecturer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="unit_assignments",
                        to="academics.academicstaffprofile",
                    ),
                ),
                (
                    "semester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lecturer_unit_assignments",
                        to="academics.semester",
                    ),
                ),
                (
                    "unit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lecturer_assignments",
                        to="academics.unit",
                    ),
                ),
            ],
            options={
                "ordering": [
                    "-semester__academic_year__starts_on",
                    "unit__code",
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="lecturerunitassignment",
            constraint=models.UniqueConstraint(
                fields=("unit", "semester"),
                name="unique_lecturer_unit_per_semester",
            ),
        ),
        migrations.CreateModel(
            name="LecturerResultSheet",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("submitted", "Submitted to HOD"),
                            ("approved", "Approved by HOD"),
                            ("returned", "Returned for Correction"),
                        ],
                        db_index=True,
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("review_notes", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "grading_scale",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="lecturer_result_sheets",
                        to="academics.gradescale",
                    ),
                ),
                (
                    "lecturer_assignment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="result_sheet",
                        to="academics.lecturerunitassignment",
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="lecturer_result_sheets_reviewed",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": [
                    "-lecturer_assignment__semester__academic_year__starts_on",
                    "lecturer_assignment__unit__code",
                ],
            },
        ),
        migrations.CreateModel(
            name="LecturerResultSheetAuditLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("created", "Sheet Created"),
                            ("marks_saved", "Marks Saved"),
                            ("submitted", "Submitted to HOD"),
                            ("approved", "Approved by HOD"),
                            ("returned", "Returned to Lecturer"),
                        ],
                        max_length=20,
                    ),
                ),
                ("details", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="lecturer_result_sheet_audit_actions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "sheet",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="audit_logs",
                        to="academics.lecturerresultsheet",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddField(
            model_name="studentgrade",
            name="lecturer_result_sheet",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="grades",
                to="academics.lecturerresultsheet",
            ),
        ),
    ]
