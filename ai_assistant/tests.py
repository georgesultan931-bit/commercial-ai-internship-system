import json
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.urls import reverse
from accounts.models import User


@override_settings(GEMINI_API_KEY="test-key", GEMINI_MODEL="gemini-3.8-flash")
class AiAssistantSecurityTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username="assistant_student", email="assistant_student@example.com", password="StrongTestPass123!", role="student", is_active=True, is_approved=True, is_email_verified=True)

    def test_chat_requires_login(self):
        self.assertEqual(self.client.post(reverse("ai_assistant:chat"), data=json.dumps({"message":"Hello"}), content_type="application/json").status_code, 302)

    def test_status_requires_login(self):
        self.assertEqual(self.client.get(reverse("ai_assistant:status")).status_code, 302)

    def test_authenticated_status(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.get(reverse("ai_assistant:status")).status_code, 200)

    def test_empty_message_rejected(self):
        self.client.force_login(self.student)
        self.assertEqual(self.client.post(reverse("ai_assistant:chat"), data=json.dumps({"message":""}), content_type="application/json").status_code, 400)

    @patch("ai_assistant.services.generate_answer")
    def test_general_question_uses_gemini_without_network(self, mocked):
        mocked.return_value = {"ok":True,"answer":"Django is a Python web framework.","sources":[]}
        self.client.force_login(self.student)
        response = self.client.post(reverse("ai_assistant:chat"), data=json.dumps({"message":"What is Django?"}), content_type="application/json")
        self.assertEqual(response.json()["answer_source"], "gemini")
        mocked.assert_called_once()

    @patch("ai_assistant.services.generate_answer")
    def test_current_question_uses_grounding(self, mocked):
        mocked.return_value = {"ok":True,"answer":"Grounded answer.","sources":[]}
        self.client.force_login(self.student)
        response = self.client.post(reverse("ai_assistant:chat"), data=json.dumps({"message":"Who is president of Kenya right now?"}), content_type="application/json")
        self.assertEqual(response.json()["answer_source"], "web")
        self.assertTrue(mocked.call_args.kwargs["use_web"])

    @patch("ai_assistant.services.generate_answer")
    def test_platform_question_never_calls_gemini(self, mocked):
        self.client.force_login(self.student)
        response = self.client.post(reverse("ai_assistant:chat"), data=json.dumps({"message":"What is my application status?"}), content_type="application/json")
        self.assertEqual(response.json()["answer_source"], "platform")
        mocked.assert_not_called()
