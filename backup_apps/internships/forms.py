from django import forms
from .models import Internship, Application
from organizations.models import Organization


class InternshipForm(forms.ModelForm):
    class Meta:
        model = Internship
        fields = [
            # 1. Internship Information
            'title', 'description', 'department', 'internship_type', 'work_mode',
            'number_of_vacancies', 'duration',
            
            # 3. Requirements
            'required_skills', 'preferred_skills', 'qualification',
            'year_of_study', 'minimum_gpa', 'preferred_course', 'experience_required',
            
            # 4. Responsibilities
            'responsibilities',
            
            # 5. Benefits
            'benefits',
            
            # 6. Salary/Stipend
            'is_paid', 'monthly_salary', 'currency', 'is_negotiable',
            
            # 7. Application Settings
            'application_deadline', 'auto_close_after_deadline', 'max_applicants',
            'allow_multiple_applications', 'require_cover_letter', 'require_cv',
            'require_transcript', 'require_certificates',
            
            # 8. AI Matching Settings
            'enable_ai_matching', 'minimum_match_score', 'auto_rank_applicants',
            'recommend_to_students',
            
            # 9. Contact Person
            'contact_name', 'contact_phone', 'contact_email',
            
            # 10. Status
            'status',
            
            # Location
            'location', 'is_remote',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Frontend Developer Intern'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the internship role...'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Engineering, Marketing'}),
            'internship_type': forms.Select(attrs={'class': 'form-control'}),
            'work_mode': forms.Select(attrs={'class': 'form-control'}),
            'number_of_vacancies': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 3 Months'}),
            'required_skills': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Python, Django, Git, SQL'}),
            'preferred_skills': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'AWS, Docker, React'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Bachelor\'s Degree'}),
            'year_of_study': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 3rd Year, Final Year'}),
            'minimum_gpa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 4}),
            'preferred_course': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Computer Science'}),
            'experience_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'responsibilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '• Develop web applications\n• Attend meetings\n• Write reports'}),
            'benefits': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '• Transport Allowance\n• Certificate\n• Mentorship'}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'monthly_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-control'}, choices=[('KES', 'KES'), ('USD', 'USD'), ('EUR', 'EUR')]),
            'is_negotiable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'application_deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'auto_close_after_deadline': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_applicants': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'allow_multiple_applications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_cover_letter': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_cv': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_transcript': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'require_certificates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_ai_matching': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'minimum_match_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'auto_rank_applicants': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'recommend_to_students': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., John Doe'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., +254 700 123 456'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'hr@company.com'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Nairobi, Kenya'}),
            'is_remote': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.organization and not self.instance.pk:
            self.fields['contact_email'].initial = self.organization.email
            self.fields['contact_name'].initial = self.user.first_name + ' ' + self.user.last_name if self.user else ''
    
    def clean_required_skills(self):
        skills = self.cleaned_data.get('required_skills', '')
        if isinstance(skills, str):
            return [s.strip() for s in skills.split(',') if s.strip()]
        return skills
    
    def clean_preferred_skills(self):
        skills = self.cleaned_data.get('preferred_skills', '')
        if isinstance(skills, str):
            return [s.strip() for s in skills.split(',') if s.strip()]
        return skills


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['cover_letter']
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Why are you interested in this internship? What makes you a good candidate?'
            }),
        }