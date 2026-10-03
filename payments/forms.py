from datetime import date

from django import forms

from .models import (
    PlacementAssistanceRequest,
    StudentVerification,
)


class StudentVerificationForm(forms.ModelForm):

    class Meta:
        model = StudentVerification

        fields = [
            "verification_method",
            "student_id_document",
        ]

        widgets = {
            "verification_method": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "student_id_document": (
                forms.ClearableFileInput(
                    attrs={
                        "class": "form-control",
                        "accept": "image/jpeg,image/png",
                        "capture": "environment",
                    }
                )
            ),
        }

        labels = {
            "verification_method": (
                "Verification method"
            ),
            "student_id_document": (
                "Student ID image"
            ),
        }

        help_texts = {
            "student_id_document": (
                "Required only when using student-ID "
                "verification. Upload a clear JPG or PNG "
                "image not exceeding 5 MB."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[
            "verification_method"
        ].choices = (
            (
                "academic_record",
                "Verify using institution academic record",
            ),
            (
                "student_id",
                "Verify using student ID",
            ),
        )

    def clean_student_id_document(self):
        document = self.cleaned_data.get(
            "student_id_document"
        )

        if document is None:
            return document

        maximum_size = 5 * 1024 * 1024

        if document.size > maximum_size:
            raise forms.ValidationError(
                "The student ID image must not exceed 5 MB."
            )

        allowed_types = {
            "image/jpeg",
            "image/png",
        }

        content_type = getattr(
            document,
            "content_type",
            "",
        )

        if (
            content_type
            and content_type not in allowed_types
        ):
            raise forms.ValidationError(
                "Upload the student ID as a JPG or PNG image."
            )

        return document

    def clean(self):
        cleaned_data = super().clean()

        method = cleaned_data.get(
            "verification_method"
        )

        document = cleaned_data.get(
            "student_id_document"
        )

        if (
            method == "student_id"
            and not document
            and not (
                self.instance.pk
                and self.instance.student_id_document
            )
        ):
            self.add_error(
                "student_id_document",
                (
                    "Upload a clear student ID image "
                    "for this verification method."
                ),
            )

        return cleaned_data


class PlacementAssistanceRequestForm(
    forms.ModelForm
):

    terms_accepted = forms.BooleanField(
        required=True,
        label=(
            "I accept the placement-assistance terms "
            "and understand that payment does not "
            "guarantee employer acceptance."
        ),
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
    )

    class Meta:
        model = PlacementAssistanceRequest

        fields = [
            "preferred_counties",
            "attachment_field",
            "placement_mode",
            "expected_start_date",
            "duration_weeks",
            "additional_requirements",
            "terms_accepted",
        ]

        widgets = {
            "preferred_counties": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Example: Kisumu, Nakuru, Nairobi"
                    ),
                }
            ),
            "attachment_field": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Example: Software Development"
                    ),
                }
            ),
            "placement_mode": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "expected_start_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "duration_weeks": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "max": 52,
                }
            ),
            "additional_requirements": (
                forms.Textarea(
                    attrs={
                        "class": "form-control",
                        "rows": 4,
                        "placeholder": (
                            "Add any important placement "
                            "requirements."
                        ),
                    }
                )
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[
            "expected_start_date"
        ].widget.attrs["min"] = date.today().isoformat()

    def clean_expected_start_date(self):
        start_date = self.cleaned_data[
            "expected_start_date"
        ]

        if start_date < date.today():
            raise forms.ValidationError(
                "The expected start date cannot be "
                "in the past."
            )

        return start_date

    def clean_preferred_counties(self):
        counties = self.cleaned_data[
            "preferred_counties"
        ]

        cleaned_counties = [
            county.strip()
            for county in counties.split(",")
            if county.strip()
        ]

        if not cleaned_counties:
            raise forms.ValidationError(
                "Enter at least one preferred county."
            )

        return ", ".join(cleaned_counties)

class PaymentInitiationForm(forms.Form):
    phone_number = forms.CharField(
        max_length=20,
        label="M-Pesa phone number",
        help_text=(
            "Enter the Safaricom number that should receive "
            "the M-Pesa payment prompt."
        ),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "0712345678",
                "inputmode": "tel",
                "autocomplete": "tel",
            }
        ),
    )

    def clean_phone_number(self):
        raw_phone = self.cleaned_data[
            "phone_number"
        ]

        phone_number = "".join(
            character
            for character in raw_phone
            if character.isdigit()
        )

        if (
            phone_number.startswith("0")
            and len(phone_number) == 10
        ):
            phone_number = (
                "254"
                + phone_number[1:]
            )

        elif (
            phone_number.startswith("7")
            and len(phone_number) == 9
        ):
            phone_number = (
                "254"
                + phone_number
            )

        elif (
            phone_number.startswith("1")
            and len(phone_number) == 9
        ):
            phone_number = (
                "254"
                + phone_number
            )

        if (
            len(phone_number) != 12
            or not phone_number.startswith(
                (
                    "2547",
                    "2541",
                )
            )
        ):
            raise forms.ValidationError(
                (
                    "Enter a valid Kenyan M-Pesa number, "
                    "for example 0712345678."
                )
            )

        return phone_number