from datetime import date

from django.test import TestCase

from accounts.models import User
from employers.models import EmployerProfile
from internships.models import InternshipOpportunity
from matching.views import (
    calculate_match_score,
    normalize_skills,
    skill_matches,
)
from students.models import StudentProfile


class MatchingEngineV2Tests(TestCase):

    def setUp(self):
        self.student_user = User.objects.create_user(
            username="student_match_test",
            email="student_match_test@example.com",
            password="StrongPass123!",
            role="student",
            is_email_verified=True,
            is_approved=True,
        )

        self.student = StudentProfile.objects.create(
            user=self.student_user,
            first_name="Match",
            surname="Student",
            course="Diploma in Computer Science",
            institution="Test Polytechnic",
            skills="Python, Django, SQL, Git",
            extracted_skills="Python, Django, REST API",
            location="Nairobi",
            town="Nairobi",
            bio="Computer science student building web applications.",
            github="https://github.com/example",
            portfolio="https://example.com",
            linkedin="https://linkedin.com/in/example",
        )

        self.employer_user = User.objects.create_user(
            username="employer_match_test",
            email="employer_match_test@example.com",
            password="StrongPass123!",
            role="employer",
            is_email_verified=True,
            is_approved=True,
        )

        self.employer = EmployerProfile.objects.create(
            user=self.employer_user,
            company_name="Test Technology Ltd",
            company_email="company@example.com",
            company_phone="0712345678",
            company_location="Nairobi",
            industry="Technology",
            company_description="Software company",
        )

    def make_opportunity(
        self,
        *,
        title="Python Developer Intern",
        required_skills="Python, Django, SQL",
        location="Nairobi",
        description="Build software and web systems using Python and Django.",
    ):
        return InternshipOpportunity.objects.create(
            employer=self.employer,
            title=title,
            internship_type="internship",
            description=description,
            required_skills=required_skills,
            location=location,
            slots_available=2,
            deadline=date(2030, 12, 31),
            status="open",
        )

    def test_normalize_skills_handles_multiple_separators_and_duplicates(self):
        result = normalize_skills(
            "Python; Django\nSQL | Python"
        )

        self.assertEqual(
            result,
            ["python", "django", "sql"]
        )

    def test_skill_matches_exact_and_phrase_forms(self):
        student_skills = [
            "python programming",
            "django framework",
            "rest api",
        ]

        self.assertTrue(
            skill_matches("Python", student_skills)
        )
        self.assertTrue(
            skill_matches("Django", student_skills)
        )
        self.assertTrue(
            skill_matches("REST API development", student_skills)
        )
        self.assertFalse(
            skill_matches("Java", student_skills)
        )

    def test_all_required_skills_do_not_exceed_skill_weight(self):
        opportunity = self.make_opportunity(
            required_skills="Python, Django, SQL, Git"
        )

        score, analysis = calculate_match_score(
            self.student,
            opportunity
        )

        self.assertEqual(
            analysis["score_breakdown"]["skills"],
            70
        )
        self.assertLessEqual(score, 100)

    def test_skill_scoring_is_normalized_by_number_of_requirements(self):
        two_skill_opportunity = self.make_opportunity(
            title="Backend Intern",
            required_skills="Python, Django",
        )

        five_skill_opportunity = self.make_opportunity(
            title="Full Stack Intern",
            required_skills="Python, Django, SQL, Java, React",
        )

        _, two_analysis = calculate_match_score(
            self.student,
            two_skill_opportunity
        )

        _, five_analysis = calculate_match_score(
            self.student,
            five_skill_opportunity
        )

        self.assertEqual(
            two_analysis["score_breakdown"]["skills"],
            70
        )

        self.assertLess(
            five_analysis["score_breakdown"]["skills"],
            70
        )

    def test_course_relevance_and_location_contribute_to_score(self):
        relevant = self.make_opportunity(
            title="Software Developer Intern",
            location="Nairobi",
            description="Software development, programming and database work.",
        )

        unrelated = self.make_opportunity(
            title="Field Agronomy Intern",
            required_skills="Crop Management, Soil Sampling",
            location="Mombasa",
            description="Agricultural field work and crop monitoring.",
        )

        relevant_score, relevant_analysis = calculate_match_score(
            self.student,
            relevant
        )
        unrelated_score, unrelated_analysis = calculate_match_score(
            self.student,
            unrelated
        )

        self.assertGreater(
            relevant_analysis["score_breakdown"]["course"],
            unrelated_analysis["score_breakdown"]["course"],
        )
        self.assertGreater(
            relevant_analysis["score_breakdown"]["location"],
            unrelated_analysis["score_breakdown"]["location"],
        )
        self.assertGreater(
            relevant_score,
            unrelated_score,
        )

    def test_missing_skills_are_explained(self):
        opportunity = self.make_opportunity(
            required_skills="Python, Django, React"
        )

        _, analysis = calculate_match_score(
            self.student,
            opportunity
        )

        self.assertIn(
            "React",
            analysis["missing_skills"]
        )
        self.assertTrue(
            any(
                "Skill gaps detected" in item
                for item in analysis["explanations"]
            )
        )

    def test_opportunity_without_required_skills_gets_neutral_skill_score(self):
        opportunity = self.make_opportunity(
            required_skills=""
        )

        _, analysis = calculate_match_score(
            self.student,
            opportunity
        )

        self.assertEqual(
            analysis["score_breakdown"]["skills"],
            35
        )
