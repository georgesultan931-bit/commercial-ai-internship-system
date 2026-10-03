from django import forms

from institutions.models import (
    PlacementProgressReport,
    SupervisorEvaluation,
)

from .models import SupervisorProfile


class SupervisorProfileForm(forms.ModelForm):

    class Meta:
        model = SupervisorProfile

        fields = [
            "institution",
            "full_name",
            "staff_number",
            "department",
            "job_title",
            "specialization",
            "phone_number",
            "official_email",
            "bio",
            "profile_picture",
        ]

        widgets = {
            "institution": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "full_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Full name",
                }
            ),

            "staff_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Staff number",
                }
            ),

            "department": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Department",
                }
            ),

            "job_title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Job title",
                }
            ),

            "specialization": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Area of specialization",
                }
            ),

            "phone_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone number",
                }
            ),

            "official_email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Official email",
                }
            ),

            "bio": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Brief professional bio",
                }
            ),

            "profile_picture": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }


class ProgressReportReviewForm(forms.ModelForm):

    class Meta:
        model = PlacementProgressReport

        fields = [
            "status",
            "supervisor_comment",
        ]

        widgets = {
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "supervisor_comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Add feedback, corrections or comments for the student...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["status"].choices = (
            ("reviewed", "Reviewed"),
            ("revision_required", "Revision Required"),
        )


class SupervisorEvaluationForm(forms.ModelForm):

    class Meta:
        model = SupervisorEvaluation

        fields = [
            "evaluation_type",
            "punctuality_score",
            "technical_skills_score",
            "communication_score",
            "teamwork_score",
            "initiative_score",
            "strengths",
            "areas_for_improvement",
            "general_comments",
            "recommendation",
        ]

        widgets = {
            "evaluation_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "punctuality_score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "max": 5,
                }
            ),

            "technical_skills_score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "max": 5,
                }
            ),

            "communication_score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "max": 5,
                }
            ),

            "teamwork_score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "max": 5,
                }
            ),

            "initiative_score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "max": 5,
                }
            ),

            "strengths": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Student strengths...",
                }
            ),

            "areas_for_improvement": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Areas where the student can improve...",
                }
            ),

            "general_comments": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "General evaluation comments...",
                }
            ),

            "recommendation": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
        }