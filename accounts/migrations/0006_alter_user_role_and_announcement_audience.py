from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0005_alter_announcement_audience_alter_user_role"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("student", "Student"),
                    ("employer", "Employer"),
                    ("institution", "Institution"),
                    ("supervisor", "Supervisor"),
                    ("lecturer", "Lecturer"),
                    ("hod", "Head of Department"),
                    ("dean", "Dean"),
                    ("admin", "Admin"),
                ],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="announcement",
            name="audience",
            field=models.CharField(
                choices=[
                    ("all", "Everyone"),
                    ("student", "Students"),
                    ("employer", "Employers"),
                    ("institution", "Institutions"),
                    ("supervisor", "Supervisors"),
                    ("lecturer", "Lecturers"),
                    ("hod", "Heads of Department"),
                    ("dean", "Deans"),
                ],
                default="all",
                max_length=20,
            ),
        ),
    ]
