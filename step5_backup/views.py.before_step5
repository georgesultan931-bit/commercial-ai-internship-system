import re

from internships.models import InternshipOpportunity


# ---------------------------------------------------------------------
# Explainable Matching Engine v2
# ---------------------------------------------------------------------
# Total score: 100
#
# Required skills ............... 70 points
# Course / opportunity relevance 15 points
# Location relevance ............  5 points
# Profile evidence .............. 10 points
#
# The engine is deterministic and explainable: every score can be traced
# to profile/opportunity data. It does not pretend to be an ML model.
# ---------------------------------------------------------------------

SKILL_WEIGHT = 70
COURSE_WEIGHT = 15
LOCATION_WEIGHT = 5
PROFILE_EVIDENCE_WEIGHT = 10

STOP_WORDS = {
    "and", "or", "the", "a", "an", "of", "for", "to", "in", "on", "with",
    "at", "by", "from", "as", "is", "are", "be", "this", "that", "role",
    "intern", "internship", "attachment", "industrial", "graduate", "trainee",
    "student", "students", "candidate", "candidates", "required", "skills",
}

# Common course-family terms used only to improve transparent keyword
# relevance. These are not hidden ML predictions.
COURSE_ALIASES = {
    "computer science": {
        "software", "developer", "development", "programming", "python",
        "django", "java", "javascript", "web", "database", "data", "systems",
        "ict", "it", "technology", "computing", "cybersecurity", "network",
    },
    "information technology": {
        "ict", "it", "technology", "support", "network", "networking",
        "systems", "database", "web", "software", "cybersecurity",
    },
    "software engineering": {
        "software", "developer", "development", "programming", "web",
        "backend", "frontend", "api", "database", "testing",
    },
    "data science": {
        "data", "analytics", "analysis", "python", "statistics", "machine",
        "learning", "database", "sql", "visualization",
    },
    "cybersecurity": {
        "security", "cybersecurity", "network", "networking", "systems",
        "risk", "audit", "incident",
    },
    "business": {
        "business", "administration", "management", "finance", "sales",
        "marketing", "operations", "customer",
    },
}


def normalize_text(value):
    """Return a clean lowercase representation suitable for comparison."""
    if value is None:
        return ""

    value = str(value).strip().lower()
    value = re.sub(r"\s+", " ", value)
    return value


def tokenize(value):
    """Convert free text to useful alphanumeric keyword tokens."""
    text = normalize_text(value)

    tokens = re.findall(r"[a-z0-9+#.]+", text)

    return {
        token
        for token in tokens
        if len(token) >= 2 and token not in STOP_WORDS
    }


def normalize_skills(skill_text):
    """
    Normalize comma/newline/semicolon/pipe-separated skills.

    Order is preserved while duplicates are removed.
    """
    if not skill_text:
        return []

    text = str(skill_text)

    for separator in ("\n", ";", "|"):
        text = text.replace(separator, ",")

    normalized = []
    seen = set()

    for raw_skill in text.split(","):
        skill = normalize_text(raw_skill)

        if skill and skill not in seen:
            seen.add(skill)
            normalized.append(skill)

    return normalized


def _skill_tokens(skill):
    return tokenize(skill)


def skill_matches(required_skill, student_skills):
    """
    Match a required skill against the student's skills.

    Matching uses:
    1. exact normalized match,
    2. phrase containment for meaningful multi-character values,
    3. token overlap for common forms such as "Django framework" vs "Django".
    """
    required = normalize_text(required_skill)

    if not required:
        return False

    required_tokens = _skill_tokens(required)

    for student_skill in student_skills:
        candidate = normalize_text(student_skill)

        if not candidate:
            continue

        if required == candidate:
            return True

        # Avoid unsafe tiny substring matches such as "c" inside "react".
        if len(required) >= 3 and len(candidate) >= 3:
            if required in candidate or candidate in required:
                return True

        candidate_tokens = _skill_tokens(candidate)

        if required_tokens and candidate_tokens:
            overlap = required_tokens & candidate_tokens

            # A single-token skill such as "python" or "django" is enough.
            if len(required_tokens) == 1 and overlap:
                return True

            # Multi-token phrases require at least half of the required terms.
            if len(required_tokens) > 1:
                ratio = len(overlap) / len(required_tokens)
                if ratio >= 0.5:
                    return True

    return False


def _course_relevance(student, opportunity):
    """
    Return a 0..1 relevance value between the student's course and the
    opportunity title/description/required skills.
    """
    course = normalize_text(getattr(student, "course", ""))

    if not course:
        return 0.0, []

    course_tokens = tokenize(course)

    opportunity_text = " ".join([
        getattr(opportunity, "title", "") or "",
        getattr(opportunity, "description", "") or "",
        getattr(opportunity, "required_skills", "") or "",
    ])
    opportunity_tokens = tokenize(opportunity_text)

    if not opportunity_tokens:
        return 0.0, []

    relevance_terms = set(course_tokens)

    for course_family, aliases in COURSE_ALIASES.items():
        family_tokens = tokenize(course_family)

        # If the course name strongly resembles a known family,
        # enrich its transparent keyword vocabulary.
        if (
            course_family in course
            or course in course_family
            or len(course_tokens & family_tokens) >= max(1, len(family_tokens) // 2)
        ):
            relevance_terms.update(aliases)

    matched_terms = sorted(relevance_terms & opportunity_tokens)

    if not relevance_terms:
        return 0.0, []

    # Course relevance should not require every alias to appear.
    # Three meaningful matches already indicate strong relevance.
    score = min(len(matched_terms) / 3, 1.0)

    return score, matched_terms


def _location_relevance(student, opportunity):
    """
    Return a 0..1 location relevance value.

    We compare opportunity location with the student's current location,
    town and home county when available.
    """
    opportunity_location = normalize_text(getattr(opportunity, "location", ""))

    if not opportunity_location:
        return 0.0, None

    student_locations = [
        getattr(student, "location", ""),
        getattr(student, "town", ""),
        getattr(student, "home_county", ""),
    ]

    opportunity_tokens = tokenize(opportunity_location)

    for location in student_locations:
        candidate = normalize_text(location)

        if not candidate:
            continue

        if candidate == opportunity_location:
            return 1.0, candidate

        if len(candidate) >= 3 and (
            candidate in opportunity_location
            or opportunity_location in candidate
        ):
            return 1.0, candidate

        candidate_tokens = tokenize(candidate)

        if candidate_tokens and opportunity_tokens & candidate_tokens:
            return 1.0, candidate

    return 0.0, None


def _profile_evidence_score(student):
    """
    Return evidence points out of PROFILE_EVIDENCE_WEIGHT and explanations.

    Evidence does not replace skill relevance; it only increases confidence
    that an employer can verify the candidate's work/background.
    """
    points = 0
    strengths = []

    if getattr(student, "cv", None):
        points += 4
        strengths.append(
            "CV uploaded, giving the employer evidence for background review."
        )

    if getattr(student, "github", None):
        points += 2
        strengths.append(
            "GitHub profile is available for technical work verification."
        )

    if getattr(student, "portfolio", None):
        points += 2
        strengths.append(
            "Portfolio website is available as project/work evidence."
        )

    if getattr(student, "linkedin", None):
        points += 1
        strengths.append(
            "LinkedIn profile is available for professional background review."
        )

    if getattr(student, "bio", None):
        points += 1
        strengths.append(
            "Profile bio provides additional candidate context."
        )

    return min(points, PROFILE_EVIDENCE_WEIGHT), strengths


def calculate_match_score(student, opportunity):
    """
    Calculate an explainable 0..100 match score.

    The score is normalized, so an opportunity requiring many skills is not
    automatically easier to score highly on than one requiring only a few.
    """
    manual_skills = normalize_skills(getattr(student, "skills", ""))

    cv_skills = normalize_skills(
        getattr(student, "extracted_skills", "")
    )

    # Preserve ordering while removing duplicate student skills.
    student_skills = list(dict.fromkeys(manual_skills + cv_skills))

    required_skills = normalize_skills(
        getattr(opportunity, "required_skills", "")
    )

    matched_skills = []
    missing_skills = []
    cv_detected_matches = []

    for required_skill in required_skills:
        if skill_matches(required_skill, student_skills):
            display_skill = required_skill.title()
            matched_skills.append(display_skill)

            if skill_matches(required_skill, cv_skills):
                cv_detected_matches.append(display_skill)
        else:
            missing_skills.append(required_skill.title())

    # ---------------------------
    # 1. Skills: maximum 70
    # ---------------------------
    if required_skills:
        skill_ratio = len(matched_skills) / len(required_skills)
        skill_points = round(skill_ratio * SKILL_WEIGHT)
    else:
        # No employer skill requirements means "unknown", not a perfect match.
        skill_ratio = 0.5
        skill_points = round(SKILL_WEIGHT * 0.5)

    # ---------------------------
    # 2. Course relevance: max 15
    # ---------------------------
    course_ratio, course_terms = _course_relevance(
        student,
        opportunity
    )
    course_points = round(course_ratio * COURSE_WEIGHT)

    # ---------------------------
    # 3. Location: max 5
    # ---------------------------
    location_ratio, matched_location = _location_relevance(
        student,
        opportunity
    )
    location_points = round(location_ratio * LOCATION_WEIGHT)

    # ---------------------------
    # 4. Evidence: max 10
    # ---------------------------
    evidence_points, evidence_strengths = _profile_evidence_score(student)

    score = min(
        skill_points
        + course_points
        + location_points
        + evidence_points,
        100,
    )

    strengths = []

    if matched_skills:
        strengths.append(
            f"Matched {len(matched_skills)} of {len(required_skills)} "
            f"required skill(s): {', '.join(matched_skills)}."
        )

    if cv_detected_matches:
        strengths.append(
            "CV-extracted skills support the match for: "
            f"{', '.join(cv_detected_matches)}."
        )

    if course_points > 0:
        strengths.append(
            f"Course background is relevant to the opportunity "
            f"({course_points}/{COURSE_WEIGHT} course points)."
        )

    if matched_location:
        strengths.append(
            f"Opportunity location aligns with the student's profile "
            f"location ({matched_location.title()})."
        )

    strengths.extend(evidence_strengths)

    explanations = [
        f"Skills: {skill_points}/{SKILL_WEIGHT}.",
        f"Course relevance: {course_points}/{COURSE_WEIGHT}.",
        f"Location relevance: {location_points}/{LOCATION_WEIGHT}.",
        f"Profile evidence: {evidence_points}/{PROFILE_EVIDENCE_WEIGHT}.",
    ]

    if required_skills:
        explanations.append(
            f"Required-skill coverage is {round(skill_ratio * 100)}% "
            f"({len(matched_skills)}/{len(required_skills)})."
        )
    else:
        explanations.append(
            "The employer did not list required skills, so the engine applies "
            "a neutral skills score instead of assuming a perfect match."
        )

    if missing_skills:
        explanations.append(
            f"Skill gaps detected: {', '.join(missing_skills)}."
        )
    else:
        explanations.append(
            "No listed required-skill gaps were detected."
        )

    if course_terms:
        explanations.append(
            "Relevant course/opportunity terms include: "
            f"{', '.join(course_terms[:8])}."
        )

    if score >= 85:
        recommendation = (
            "Excellent match. Strong candidate for priority review/interview."
        )
        match_level = "excellent"
    elif score >= 70:
        recommendation = (
            "Strong match. Suitable for shortlisting."
        )
        match_level = "strong"
    elif score >= 50:
        recommendation = (
            "Moderate match. Review the candidate profile and CV."
        )
        match_level = "moderate"
    else:
        recommendation = (
            "Low match. Significant gaps or limited supporting evidence exist."
        )
        match_level = "low"

    explanations.append(
        f"Overall recommendation: {recommendation}"
    )

    return score, {
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "cv_detected_matches": cv_detected_matches,
        "strengths": strengths,
        "explanations": explanations,
        "match_level": match_level,
        "score_breakdown": {
            "skills": skill_points,
            "skills_max": SKILL_WEIGHT,
            "course": course_points,
            "course_max": COURSE_WEIGHT,
            "location": location_points,
            "location_max": LOCATION_WEIGHT,
            "evidence": evidence_points,
            "evidence_max": PROFILE_EVIDENCE_WEIGHT,
        },
    }


def get_matched_opportunities(student):
    """
    Return open opportunities ranked from highest to lowest match score.
    """
    opportunities = InternshipOpportunity.objects.filter(
        status="open"
    ).select_related("employer", "employer__user")

    matched_results = []

    for opportunity in opportunities:
        score, analysis = calculate_match_score(
            student,
            opportunity
        )

        matched_results.append({
            "opportunity": opportunity,
            "score": score,
            "matched_skills": analysis["matched_skills"],
            "missing_skills": analysis["missing_skills"],
            "strengths": analysis["strengths"],
            "explanations": analysis["explanations"],
            "match_level": analysis["match_level"],
            "score_breakdown": analysis["score_breakdown"],
        })

    matched_results.sort(
        key=lambda item: (
            item["score"],
            len(item["matched_skills"]),
            -len(item["missing_skills"]),
        ),
        reverse=True,
    )

    return matched_results
