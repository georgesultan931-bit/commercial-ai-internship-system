from django import forms
from django.forms import formset_factory

from .models import (
    GradeAmendmentRequest,
    GradeBand,
    GradeScale,
    Semester,
    StudentUnitRegistration,
    Unit,
)


class GradeScaleForm(forms.ModelForm):
    class Meta:
        model = GradeScale
        fields = (
            "name",
            "coursework_weight",
            "examination_weight",
            "pass_mark",
            "is_default",
            "is_active",
        )
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "coursework_weight": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "examination_weight": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "pass_mark": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "is_default": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class GradeBandForm(forms.ModelForm):
    class Meta:
        model = GradeBand
        fields = (
            "minimum_mark",
            "maximum_mark",
            "letter_grade",
            "grade_point",
            "remark",
            "is_pass",
        )
        widgets = {
            "minimum_mark": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "maximum_mark": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "letter_grade": forms.TextInput(attrs={"class": "form-control"}),
            "grade_point": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "remark": forms.TextInput(attrs={"class": "form-control"}),
            "is_pass": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SemesterSubmissionSetupForm(forms.Form):
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    grading_scale = forms.ModelChoiceField(
        queryset=GradeScale.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, assignment, **kwargs):
        super().__init__(*args, **kwargs)
        self.assignment = assignment
        self.fields["semester"].queryset = (
            Semester.objects.filter(
                academic_year__institution=assignment.institution,
            )
            .select_related("academic_year")
            .order_by("-academic_year__starts_on", "number")
        )
        self.fields["grading_scale"].queryset = GradeScale.objects.filter(
            institution=assignment.institution,
            is_active=True,
        ).order_by("-is_default", "name")


class UnitRegistrationForm(forms.Form):
    semester = forms.ModelChoiceField(
        queryset=Semester.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    study_year = forms.IntegerField(
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    units = forms.ModelMultipleChoiceField(
        queryset=Unit.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
    )

    def __init__(self, *args, assignment, **kwargs):
        super().__init__(*args, **kwargs)
        self.assignment = assignment
        self.fields["semester"].queryset = (
            Semester.objects.filter(
                academic_year__institution=assignment.institution,
            )
            .select_related("academic_year")
            .order_by("-academic_year__starts_on", "number")
        )

        units = Unit.objects.none()

        if assignment.programme_id:
            selected_semester = self.initial.get("semester")
            selected_study_year = self.initial.get(
                "study_year",
                assignment.year_of_study,
            )

            if self.is_bound:
                semester_id = self.data.get(self.add_prefix("semester"))
                selected_semester = self.fields["semester"].queryset.filter(
                    pk=semester_id,
                ).first()
                selected_study_year = self.data.get(
                    self.add_prefix("study_year"),
                    assignment.year_of_study,
                )

            try:
                selected_study_year = int(selected_study_year)
            except (TypeError, ValueError):
                selected_study_year = assignment.year_of_study

            units = Unit.objects.filter(
                programme=assignment.programme,
                year_of_study=selected_study_year,
                is_active=True,
            )

            if isinstance(selected_semester, Semester):
                units = units.filter(
                    semester_number=selected_semester.number,
                )

            units = units.order_by("code")

        self.fields["units"].queryset = units
        self.fields["study_year"].initial = assignment.year_of_study

    def clean(self):
        cleaned_data = super().clean()
        semester = cleaned_data.get("semester")
        study_year = cleaned_data.get("study_year")
        units = cleaned_data.get("units")

        if not semester or study_year is None or units is None:
            return cleaned_data

        invalid_units = [
            unit.code
            for unit in units
            if (
                unit.programme_id != self.assignment.programme_id
                or unit.year_of_study != study_year
                or unit.semester_number != semester.number
            )
        ]

        if invalid_units:
            raise forms.ValidationError(
                "These units do not match the selected programme, year and "
                f"semester: {', '.join(invalid_units)}."
            )

        return cleaned_data


class GradeEntryForm(forms.Form):
    registration_id = forms.IntegerField(widget=forms.HiddenInput())
    coursework_mark = forms.DecimalField(
        min_value=0,
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "0.01"}
        ),
    )
    examination_mark = forms.DecimalField(
        min_value=0,
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "0.01"}
        ),
    )

    def __init__(self, *args, submission, **kwargs):
        super().__init__(*args, **kwargs)
        self.submission = submission
        scale = submission.grading_scale
        self.fields["coursework_mark"].max_value = scale.coursework_weight
        self.fields["examination_mark"].max_value = scale.examination_weight
        self.fields["coursework_mark"].widget.attrs["max"] = str(
            scale.coursework_weight
        )
        self.fields["examination_mark"].widget.attrs["max"] = str(
            scale.examination_weight
        )

    def clean_registration_id(self):
        registration_id = self.cleaned_data["registration_id"]

        registration = (
            StudentUnitRegistration.objects.filter(
                pk=registration_id,
                assignment=self.submission.assignment,
                semester=self.submission.semester,
                is_active=True,
            )
            .select_related("unit")
            .first()
        )

        if registration is None:
            raise forms.ValidationError(
                "This unit registration is not valid for the selected student."
            )

        self.registration = registration
        return registration_id


GradeEntryFormSet = formset_factory(
    GradeEntryForm,
    extra=0,
    can_delete=False,
)


class ResultSubmissionForm(forms.Form):
    confirmation = forms.BooleanField(
        required=True,
        label=(
            "I confirm that all marks are accurate and ready for Dean review."
        ),
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


class DeanResultReviewForm(forms.Form):
    ACTION_CHOICES = (
        ("publish", "Approve and publish to student"),
        ("return", "Return to HOD for correction"),
    )

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(),
    )
    review_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Dean comments or correction instructions",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()

        if (
            cleaned_data.get("action") == "return"
            and not cleaned_data.get("review_notes", "").strip()
        ):
            self.add_error(
                "review_notes",
                "Explain the corrections required before returning results.",
            )

        return cleaned_data


class GradeAmendmentRequestForm(forms.ModelForm):
    class Meta:
        model = GradeAmendmentRequest
        fields = (
            "proposed_coursework_mark",
            "proposed_examination_mark",
            "reason",
        )
        widgets = {
            "proposed_coursework_mark": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "proposed_examination_mark": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "reason": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "State why the published grade must change",
                }
            ),
        }

    def __init__(self, *args, grade, **kwargs):
        super().__init__(*args, **kwargs)
        self.grade = grade
        scale = grade.submission.grading_scale
        self.fields["proposed_coursework_mark"].initial = grade.coursework_mark
        self.fields["proposed_examination_mark"].initial = grade.examination_mark
        self.fields["proposed_coursework_mark"].widget.attrs["max"] = str(
            scale.coursework_weight
        )
        self.fields["proposed_examination_mark"].widget.attrs["max"] = str(
            scale.examination_weight
        )

    def save(self, commit=True):
        amendment = super().save(commit=False)
        amendment.grade = self.grade

        if commit:
            amendment.save()

        return amendment


class GradeAmendmentReviewForm(forms.Form):
    ACTION_CHOICES = (
        ("approve", "Approve and apply amendment"),
        ("reject", "Reject amendment"),
    )

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(),
    )
    review_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 4}
        ),
    )

    def clean(self):
        cleaned_data = super().clean()

        if (
            cleaned_data.get("action") == "reject"
            and not cleaned_data.get("review_notes", "").strip()
        ):
            self.add_error(
                "review_notes",
                "Give a reason for rejecting the amendment.",
            )

        return cleaned_data


class LecturerGradeEntryForm(forms.Form):
    registration_id = forms.IntegerField(widget=forms.HiddenInput())
    coursework_mark = forms.DecimalField(
        min_value=0,
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "0.01"}
        ),
    )
    examination_mark = forms.DecimalField(
        min_value=0,
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "step": "0.01"}
        ),
    )

    def __init__(self, *args, lecturer_assignment, grading_scale, **kwargs):
        super().__init__(*args, **kwargs)
        self.lecturer_assignment = lecturer_assignment
        self.grading_scale = grading_scale
        self.fields["coursework_mark"].max_value = grading_scale.coursework_weight
        self.fields["examination_mark"].max_value = grading_scale.examination_weight
        self.fields["coursework_mark"].widget.attrs["max"] = str(
            grading_scale.coursework_weight
        )
        self.fields["examination_mark"].widget.attrs["max"] = str(
            grading_scale.examination_weight
        )

    def clean_registration_id(self):
        registration_id = self.cleaned_data["registration_id"]
        assignment = self.lecturer_assignment
        registration = (
            StudentUnitRegistration.objects.filter(
                pk=registration_id,
                unit=assignment.unit,
                semester=assignment.semester,
                assignment__department=assignment.unit.programme.department,
                assignment__institution=(
                    assignment.semester.academic_year.institution
                ),
                is_active=True,
            )
            .select_related("assignment", "assignment__student", "unit")
            .first()
        )

        if registration is None:
            raise forms.ValidationError(
                "This student registration does not belong to your assigned unit."
            )

        self.registration = registration
        return registration_id


LecturerGradeEntryFormSet = formset_factory(
    LecturerGradeEntryForm,
    extra=0,
    can_delete=False,
)


class LecturerSheetSubmissionForm(forms.Form):
    confirmation = forms.BooleanField(
        required=True,
        label="I confirm that this unit's marks are complete and accurate.",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )


class HODLecturerSheetReviewForm(forms.Form):
    ACTION_CHOICES = (
        ("approve", "Approve unit marks"),
        ("return", "Return to Lecturer"),
    )

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(),
    )
    review_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Correction instructions or review notes",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get("action") == "return"
            and not cleaned_data.get("review_notes", "").strip()
        ):
            self.add_error(
                "review_notes",
                "Explain the corrections required before returning the marks.",
            )
        return cleaned_data
