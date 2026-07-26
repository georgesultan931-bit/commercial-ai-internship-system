import os
import re
import json
import PyPDF2
from docx import Document
from django.conf import settings
from django.contrib.auth.models import User
from internships.models import Internship, Application
from .models import ResumeAnalysis, AIRecommendation, CandidateRanking

# Try to import sklearn, fallback if not available
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class AIService:
    """Simplified AI Service"""
    
    def __init__(self):
        self.is_ready = True
        self.vectorizer = None
    
    def extract_text_from_pdf(self, file_path):
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path):
        """Extract text from DOCX file"""
        try:
            doc = Document(file_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except Exception as e:
            print(f"Error reading DOCX: {e}")
            return ""
    
    def extract_skills(self, text):
        """Extract skills from text using keyword matching"""
        skills_list = [
            'python', 'django', 'react', 'angular', 'vue', 'node', 'express',
            'postgresql', 'mysql', 'mongodb', 'redis', 'docker', 'kubernetes',
            'aws', 'azure', 'gcp', 'linux', 'git', 'github', 'jenkins',
            'javascript', 'typescript', 'html', 'css', 'sass', 'tailwind',
            'java', 'spring', 'c++', 'c#', 'php', 'laravel', 'ruby', 'rails',
            'machine learning', 'artificial intelligence', 'deep learning',
            'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch',
            'excel', 'powerpoint', 'word', 'project management',
            'agile', 'scrum', 'communication', 'leadership', 'teamwork',
            'problem solving', 'critical thinking', 'adaptability',
            'sql', 'nosql', 'tableau', 'power bi', 'figma', 'sketch', 'adobe',
            'photoshop', 'illustrator', 'indesign', 'blender', 'unity',
            'game development', 'cybersecurity', 'networking', 'cloud computing'
        ]
        
        text_lower = text.lower()
        found_skills = []
        for skill in skills_list:
            if skill in text_lower:
                found_skills.append(skill)
        
        return list(set(found_skills))  # Remove duplicates
    
    def extract_experience(self, text):
        """Extract experience information from text"""
        experience = []
        lines = text.split('\n')
        
        keywords = ['experience', 'worked', 'intern', 'assistant', 'developer', 'designer', 
                   'manager', 'engineer', 'analyst', 'consultant', 'coordinator']
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in keywords) and len(line) > 20:
                experience.append(line)
                if len(experience) >= 10:
                    break
        
        return experience
    
    def extract_education(self, text):
        """Extract education information from text"""
        education = []
        lines = text.split('\n')
        
        education_keywords = ['university', 'college', 'institute', 'school', 'degree', 
                              'bachelor', 'master', 'phd', 'diploma', 'certification']
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in education_keywords) and len(line) > 10:
                education.append(line)
                if len(education) >= 5:
                    break
        
        return education
    
    def analyze_resume(self, user, resume_file):
        """Analyze a resume and extract information"""
        file_path = resume_file.path
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Extract text based on file type
        if file_ext == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif file_ext == '.docx':
            text = self.extract_text_from_docx(file_path)
        else:
            return {'error': 'Unsupported file format. Please upload PDF or DOCX.'}
        
        if not text:
            return {'error': 'Could not extract text from file. Please try another file.'}
        
        # Extract information
        skills = self.extract_skills(text)
        experience = self.extract_experience(text)
        education = self.extract_education(text)
        
        # Save to database
        analysis, created = ResumeAnalysis.objects.update_or_create(
            user=user,
            defaults={
                'resume_file': resume_file,
                'extracted_text': text[:5000],
                'skills': skills,
                'experience': experience,
                'education': education,
            }
        )
        
        return {
            'success': True,
            'skills': skills,
            'experience': experience[:5],
            'education': education[:3],
            'text_preview': text[:300] + '...' if len(text) > 300 else text,
            'skill_count': len(skills),
        }
    
    def calculate_similarity(self, text1, text2):
        """Calculate similarity between two texts using TF-IDF if available"""
        if not text1 or not text2:
            return 0
        
        if SKLEARN_AVAILABLE:
            try:
                vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
                tfidf_matrix = vectorizer.fit_transform([text1, text2])
                similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
                return float(similarity[0][0])
            except:
                pass
        
        # Fallback: simple keyword overlap
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0
        common = len(words1.intersection(words2))
        total = len(words1) + len(words2)
        return common / total if total > 0 else 0
    
    def match_student_to_internship(self, student, internship):
        """Calculate match score between a student and an internship"""
        try:
            # Get student skills
            try:
                resume = ResumeAnalysis.objects.get(user=student)
                student_skills = resume.skills or []
                student_text = resume.extracted_text or ''
            except ResumeAnalysis.DoesNotExist:
                student_skills = []
                student_text = ''
            
            # Get internship requirements
            required_skills = internship.required_skills or []
            description = internship.description or ''
            
            # Calculate skill match
            if required_skills and student_skills:
                matched_skills = [s for s in required_skills if s.lower() in [sk.lower() for sk in student_skills]]
                skill_match = len(matched_skills) / len(required_skills)
            else:
                skill_match = 0
                matched_skills = []
            
            # Calculate text similarity
            if student_text and description:
                semantic_similarity = self.calculate_similarity(student_text, description)
            else:
                semantic_similarity = 0
            
            # Combined score: 70% skill match + 30% semantic similarity
            final_score = (skill_match * 0.7) + (semantic_similarity * 0.3)
            final_score = round(min(final_score * 100, 100), 2)  # Convert to percentage, max 100%
            
            return {
                'score': final_score,
                'skill_match': round(skill_match * 100, 2),
                'semantic_similarity': round(semantic_similarity * 100, 2),
                'matched_skills': matched_skills,
            }
            
        except Exception as e:
            print(f"Error in match_student_to_internship: {e}")
            return {'score': 0, 'error': str(e)}
    
    def rank_candidates(self, internship):
        """Rank all applicants for an internship"""
        applications = Application.objects.filter(
            internship=internship,
            status__in=['APPLIED', 'REVIEWING']
        )
        
        if not applications:
            return {'applications': []}
        
        results = []
        for app in applications:
            match_result = self.match_student_to_internship(app.applicant, internship)
            results.append({
                'application': app,
                'applicant': app.applicant,
                'match_score': match_result.get('score', 0),
                'details': match_result,
            })
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Update rankings in database
        for idx, result in enumerate(results):
            ranking, created = CandidateRanking.objects.update_or_create(
                application=result['application'],
                defaults={
                    'match_score': result['match_score'],
                    'overall_rank': idx + 1,
                }
            )
        
        return {
            'applications': results,
            'total': len(results),
        }
    
    def get_recommendations_for_student(self, student, limit=5):
        """Get internship recommendations for a student"""
        # Get internships student hasn't applied to
        applied_ids = Application.objects.filter(applicant=student).values_list('internship_id', flat=True)
        
        internships = Internship.objects.filter(
            status='APPROVED'
        ).exclude(
            id__in=applied_ids
        )[:20]
        
        if not internships:
            return {'recommendations': []}
        
        recommendations = []
        for internship in internships:
            match_result = self.match_student_to_internship(student, internship)
            score = match_result.get('score', 0)
            
            if score > 20:  # Only recommend if score is decent
                recommendations.append({
                    'internship': internship,
                    'score': score,
                    'details': match_result,
                })
        
        # Sort by score
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'recommendations': recommendations[:limit],
            'total': len(recommendations),
        }