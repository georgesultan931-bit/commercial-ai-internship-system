from django import forms
from django.db.models import Q

from internships.models import Application
from students.models import StudentProfile
from supervisors.models import SupervisorProfile

from .models import InstitutionProfile, PlacementAssignment


class InstitutionProfileForm(forms.ModelForm):
    class Meta:
        model = InstitutionProfile

        fields = [
            "institution_name",
            "institution_type",
            "registration_number",
            "official_email",
            "phone_number",
            "website",
            "address",
            "county",
            "town",
            "contact_person_name",
            "contact_person_position",
            "description",
            "logo",
        ]

        widgets = {
            "institution_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Institution name",
                }
            ),
            "institution_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "registration_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Registration number",
                }
            ),
            "official_email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Official email address",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone number",
                }
            ),
            "website": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://example.ac.ke",
                }
            ),
            "address": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Physical or postal address",
                }
            ),
            "county": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "County",
                }
            ),
            "town": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Town",
                }
            ),
            "contact_person_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Contact person",
                }
            ),
            "contact_person_position": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Position / title",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Brief description of the institution",
                }
            ),
            "logo": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }


class PlacementAssignmentForm(forms.ModelForm):

    class Meta:
        model = PlacementAssignment

        fields = [
            "student",
            "supervisor",
            "application",
            "status",
            "start_date",
            "end_date",
            "institution_notes",
        ]

        widgets = {
            "student": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "supervisor": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "application": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "start_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "institution_notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Optional institution notes",
                }
            ),
        }

    def __init__(self, *args, institution=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.institution = institution

        self.fields["student"].queryset = StudentProfile.objects.none()
        self.fields["supervisor"].queryset = SupervisorProfile.objects.none()
        self.fields["application"].queryset = Application.objects.none()

        self.fields["supervisor"].required = False
        self.fields["application"].required = False

        if not institution:
            return

        current_student_id = None
        current_supervisor_id = None
        current_application_id = None

        if self.instance and self.instance.pk:
            current_student_id = self.instance.student_id
            current_supervisor_id = self.instance.supervisor_id
            current_application_id = self.instance.application_id

        # ---------------------------------------------------------
        # STUDENTS
        # Only students linked to this InstitutionProfile.
        # Existing linked student is preserved during editing.
        # ---------------------------------------------------------

        student_filter = Q(
            institution_profile=institution
        )

        if current_student_id:
            student_filter |= Q(
                pk=current_student_id
            )

        self.fields["student"].queryset = (
            StudentProfile.objects
            .filter(student_filter)
            .select_related(
                "user",
                "institution_profile",
            )
            .distinct()
            .order_by(
                "full_name",
                "user__username",
            )
        )

        # ---------------------------------------------------------
        # SUPERVISORS
        # Only active, approved supervisors from this institution.
        # Existing supervisor is preserved when editing.
        # ---------------------------------------------------------

        supervisor_filter = (
            Q(institution=institution)
            & Q(user__role="supervisor")
            & Q(user__is_approved=True)
            & Q(user__is_active=True)
        )

        if current_supervisor_id:
            supervisor_filter |= Q(
                pk=current_supervisor_id,
                institution=institution,
            )

        self.fields["supervisor"].queryset = (
            SupervisorProfile.objects
            .filter(supervisor_filter)
            .select_related(
                "user",
                "institution",
            )
            .distinct()
            .order_by("full_name")
        )

        # ---------------------------------------------------------
        # APPLICATIONS
        # Only accepted applications belonging to students linked
        # to this institution, and not already used elsewhere.
        # ---------------------------------------------------------

        application_filter = (
            Q(status="accepted")
            & Q(
                student__institution_profile=institution
            )
        )

        available_application_filter = Q(
            placement_assignment__isnull=True
        )

        if current_application_id:
            available_application_filter |= Q(
                pk=current_application_id
            )

        self.fields["application"].queryset = (
            Application.objects
            .filter(application_filter)
            .filter(available_application_filter)
            .select_related(
                "student",
                "student__user",
                "student__institution_profile",
                "opportunity",
                "opportunity__employer",
            )
            .distinct()
            .order_by("-applied_at")
        )

    def clean(self):
        cleaned_data = super().clean()

        student = cleaned_data.get("student")
        supervisor = cleaned_data.get("supervisor")
        application = cleaned_data.get("application")
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if not self.institution:
            raise forms.ValidationError(
                "Institution information is required to create "
                "or update a placement."
            )

        # ---------------------------------------------------------
        # Student ownership
        # ---------------------------------------------------------

        if student:
            is_current_student = (
                self.instance
                and self.instance.pk
                and self.instance.student_id == student.id
            )

            if (
                not is_current_student
                and student.institution_profile_id
                != self.institution.id
            ):
                self.add_error(
                    "student",
                    (
                        "You can only assign students linked "
                        "to your institution."
                    )
                )

        # ---------------------------------------------------------
        # Supervisor ownership / approval
        # ---------------------------------------------------------

        if supervisor:
            if supervisor.institution_id != self.institution.id:
                self.add_error(
                    "supervisor",
                    (
                        "You can only assign supervisors from "
                        "your institution."
                    )
                )

            is_current_supervisor = (
                self.instance
                and self.instance.pk
                and self.instance.supervisor_id == supervisor.id
            )

            if not is_current_supervisor:
                supervisor_user = supervisor.user

                if (
                    supervisor_user.role != "supervisor"
                    or not supervisor_user.is_approved
                    or not supervisor_user.is_active
                ):
                    self.add_error(
                        "supervisor",
                        (
                            "The selected supervisor is not an "
                            "active approved supervisor."
                        )
                    )

        # ---------------------------------------------------------
        # Application validation
        # ---------------------------------------------------------

        if application:
            if application.status != "accepted":
                self.add_error(
                    "application",
                    (
                        "Only accepted internship applications "
                        "can be linked to a placement."
                    )
                )

            if student and application.student_id != student.id:
                self.add_error(
                    "application",
                    (
                        "The selected application does not "
                        "belong to this student."
                    )
                )

            is_current_application = (
                self.instance
                and self.instance.pk
                and self.instance.application_id == application.id
            )

            if (
                not is_current_application
                and application.student.institution_profile_id
                != self.institution.id
            ):
                self.add_error(
                    "application",
                    (
                        "This application does not belong to "
                        "a student from your institution."
                    )
                )

            existing_application_assignment = (
                PlacementAssignment.objects
                .filter(application=application)
            )

            if self.instance and self.instance.pk:
                existing_application_assignment = (
                    existing_application_assignment.exclude(
                        pk=self.instance.pk
                    )
                )

            if existing_application_assignment.exists():
                self.add_error(
                    "application",
                    (
                        "This application is already linked "
                        "to another placement."
                    )
                )

        # ---------------------------------------------------------
        # Dates
        # ---------------------------------------------------------

        if start_date and end_date:
            if end_date < start_date:
                self.add_error(
                    "end_date",
                    (
                        "End date cannot be earlier than "
                        "the start date."
                    )
                )

        # ---------------------------------------------------------
        # Duplicate placement protection
        # ---------------------------------------------------------

        if student:
            duplicate_query = (
                PlacementAssignment.objects
                .filter(
                    institution=self.institution,
                    student=student,
                )
            )

            if application:
                duplicate_query = duplicate_query.filter(
                    application=application
                )
            else:
                duplicate_query = duplicate_query.filter(
                    application__isnull=True
                )

            if self.instance and self.instance.pk:
                duplicate_query = duplicate_query.exclude(
                    pk=self.instance.pk
                )

            if duplicate_query.exists():
                raise forms.ValidationError(
                    (
                        "This student already has the same "
                        "placement assignment under your "
                        "institution."
                    )
                )

        return cleaned_data