$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\manage.py")) {
    Write-Host "ERROR: Run this script from the backend folder containing manage.py." -ForegroundColor Red
    exit 1
}

Write-Host "Installing Step 5B Match Score UI..." -ForegroundColor Cyan

$backupDir = ".\step5b_backup"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

$targets = @(
    ".\templates\internships\opportunity_list.html",
    ".\templates\internships\opportunity_detail.html",
    ".\templates\internships\employer_applications.html",
    ".\templates\internships\application_detail.html",
    ".\internships\views.py"
)

foreach ($target in $targets) {
    if (Test-Path $target) {
        $safe = ($target -replace "[\\.:]", "_").Trim("_")
        Copy-Item $target (Join-Path $backupDir ($safe + ".before_step5b")) -Force
    }
}

$OpportunityList = @'
{% extends 'base.html' %}

{% block content %}

<style>
.opportunity-card{
    border:none;
    border-radius:28px;
    box-shadow:0 15px 35px rgba(15,23,42,.08);
    transition:.25s;
}

.opportunity-card:hover{
    transform:translateY(-5px);
}

.company-logo{
    width:70px;
    height:70px;
    border-radius:18px;
    object-fit:cover;
    border:3px solid #e5e7eb;
}

.skill-badge{
    border-radius:50px;
    padding:8px 12px;
}

.match-breakdown{
    background:#f8fafc;
    border:1px solid #e2e8f0;
    border-radius:18px;
    padding:14px;
}

.breakdown-item{
    background:white;
    border:1px solid #e2e8f0;
    border-radius:14px;
    padding:10px 8px;
    text-align:center;
    height:100%;
}

.breakdown-item strong{
    display:block;
    font-size:18px;
    color:#0f172a;
}

.breakdown-item small{
    color:#64748b;
    font-size:11px;
}

.match-level-badge{
    border-radius:50px;
    padding:7px 12px;
    font-size:11px;
    text-transform:uppercase;
    letter-spacing:.04em;
}
</style>

<h1 class="mb-4 fw-bold">
    Recommended Opportunities
</h1>

<form method="get" class="mb-4">

    <div class="input-group">

        <input type="text"
               name="q"
               class="form-control"
               placeholder="Search jobs, companies, locations..."
               value="{{ query }}">

        <button class="btn btn-dark">
            Search
        </button>

    </div>

</form>

<div class="row g-4">

{% for result in matched_results %}

<div class="col-lg-6">

    <div class="card opportunity-card h-100">

        <div class="card-body p-4">

            <div class="d-flex align-items-center gap-3 mb-4">

                {% if result.opportunity.employer.logo %}

                    <img src="{{ result.opportunity.employer.logo.url }}"
                         class="company-logo">

                {% else %}

                    <div class="company-logo d-flex align-items-center justify-content-center bg-light">
                        <i class="bi bi-building fs-3"></i>
                    </div>

                {% endif %}

                <div>

                    <h5 class="fw-bold mb-1">
                        {{ result.opportunity.title }}
                    </h5>

                    <small class="text-muted">
                        {{ result.opportunity.employer.company_name }}
                    </small>

                </div>

            </div>

            <div class="mb-4">

                <div class="d-flex justify-content-between">

                    <strong>Smart Match Score</strong>

                    <strong>
                        {{ result.score }}%
                    </strong>

                </div>

                <div class="progress mt-2"
                     style="height:12px;">

                    {% if result.score >= 80 %}

                        <div class="progress-bar bg-success"
                             style="width:{{ result.score }}%">
                        </div>

                    {% elif result.score >= 50 %}

                        <div class="progress-bar bg-warning"
                             style="width:{{ result.score }}%">
                        </div>

                    {% else %}

                        <div class="progress-bar bg-danger"
                             style="width:{{ result.score }}%">
                        </div>

                    {% endif %}

                </div>

            </div>

            <div class="match-breakdown mb-4">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <small class="fw-bold text-muted text-uppercase">Score Breakdown</small>

                    {% if result.match_level == 'excellent' %}
                        <span class="badge bg-success match-level-badge">Excellent Match</span>
                    {% elif result.match_level == 'strong' %}
                        <span class="badge bg-primary match-level-badge">Strong Match</span>
                    {% elif result.match_level == 'moderate' %}
                        <span class="badge bg-warning text-dark match-level-badge">Moderate Match</span>
                    {% else %}
                        <span class="badge bg-secondary match-level-badge">Low Match</span>
                    {% endif %}
                </div>

                <div class="row g-2">
                    <div class="col-6 col-md-3"><div class="breakdown-item"><strong>{{ result.score_breakdown.skills }}/{{ result.score_breakdown.skills_max }}</strong><small>Skills</small></div></div>
                    <div class="col-6 col-md-3"><div class="breakdown-item"><strong>{{ result.score_breakdown.course }}/{{ result.score_breakdown.course_max }}</strong><small>Course</small></div></div>
                    <div class="col-6 col-md-3"><div class="breakdown-item"><strong>{{ result.score_breakdown.location }}/{{ result.score_breakdown.location_max }}</strong><small>Location</small></div></div>
                    <div class="col-6 col-md-3"><div class="breakdown-item"><strong>{{ result.score_breakdown.evidence }}/{{ result.score_breakdown.evidence_max }}</strong><small>Evidence</small></div></div>
                </div>
            </div>

            <div class="mb-3">

                <span class="badge bg-primary">
                    {{ result.opportunity.get_internship_type_display }}
                </span>

                <span class="badge bg-secondary">
                    {{ result.opportunity.location }}
                </span>

            </div>

            <div class="mb-3">

                <p class="mb-1">
                    <strong>Employer Required Skills:</strong>
                </p>

                <p class="text-muted small mb-3">
                    {{ result.opportunity.required_skills }}
                </p>

                <div class="mb-2">
                    <small class="fw-bold text-success d-block mb-2">
                        Skills You Meet
                    </small>

                    {% for skill in result.matched_skills %}

                        <span class="badge bg-success skill-badge">
                            {{ skill }}
                        </span>

                    {% empty %}

                        <span class="text-muted small">
                            No required skills matched yet.
                        </span>

                    {% endfor %}
                </div>

                <div>
                    <small class="fw-bold text-danger d-block mb-2">
                        Skills Still Missing
                    </small>

                    {% for skill in result.missing_skills %}

                        <span class="badge bg-danger skill-badge">
                            {{ skill }}
                        </span>

                    {% empty %}

                        <span class="text-success small">
                            You meet all listed required skills.
                        </span>

                    {% endfor %}
                </div>

            </div>

            <p>
                <strong>Deadline:</strong>
                {{ result.opportunity.deadline }}
            </p>

            <p>
                <strong>Available Slots:</strong>
                {{ result.opportunity.slots_available }}
            </p>

            <div class="d-flex gap-2 flex-wrap">

                <a href="{% url 'opportunity_detail' result.opportunity.id %}"
                   class="btn btn-outline-dark">
                    View Details
                </a>

                {% if result.already_applied %}

                    <button class="btn btn-secondary" disabled>
                        Already Applied
                    </button>

                {% else %}

                    <a href="{% url 'apply_opportunity' result.opportunity.id %}"
                       class="btn btn-primary">
                        Apply Now
                    </a>

                {% endif %}

            </div>

        </div>

    </div>

</div>

{% empty %}

<div class="alert alert-warning">
    No recommended opportunities available.
</div>

{% endfor %}

</div>

{% endblock %}

'@
$OpportunityDetail = @'
{% extends 'base.html' %}

{% block content %}

<h1 class="mb-4 fw-bold">
    {{ opportunity.title }}
</h1>

<div class="card shadow border-0">

    <div class="card-body">

        <div class="mb-4">

            <div class="d-flex justify-content-between mb-2">

                <strong>
                    Smart Match Score
                </strong>

                <span class="fw-bold">
                    {{ score }}%
                </span>

            </div>

            <div class="progress"
                 style="height: 12px;">

                {% if score >= 70 %}

                    <div class="progress-bar bg-success"
                         style="width: {{ score }}%;">
                    </div>

                {% elif score >= 40 %}

                    <div class="progress-bar bg-warning"
                         style="width: {{ score }}%;">
                    </div>

                {% else %}

                    <div class="progress-bar bg-danger"
                         style="width: {{ score }}%;">
                    </div>

                {% endif %}

            </div>

        </div>

        <div class="card border-0 bg-light mb-4">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
                    <h5 class="fw-bold mb-0">Score Breakdown</h5>
                    {% if match_level == 'excellent' %}
                        <span class="badge bg-success">Excellent Match</span>
                    {% elif match_level == 'strong' %}
                        <span class="badge bg-primary">Strong Match</span>
                    {% elif match_level == 'moderate' %}
                        <span class="badge bg-warning text-dark">Moderate Match</span>
                    {% else %}
                        <span class="badge bg-secondary">Low Match</span>
                    {% endif %}
                </div>

                <div class="row g-3 text-center">
                    <div class="col-6 col-md-3"><div class="bg-white rounded-4 border p-3 h-100"><div class="fw-bold fs-5">{{ score_breakdown.skills }}/{{ score_breakdown.skills_max }}</div><small class="text-muted">Required Skills</small></div></div>
                    <div class="col-6 col-md-3"><div class="bg-white rounded-4 border p-3 h-100"><div class="fw-bold fs-5">{{ score_breakdown.course }}/{{ score_breakdown.course_max }}</div><small class="text-muted">Course Relevance</small></div></div>
                    <div class="col-6 col-md-3"><div class="bg-white rounded-4 border p-3 h-100"><div class="fw-bold fs-5">{{ score_breakdown.location }}/{{ score_breakdown.location_max }}</div><small class="text-muted">Location</small></div></div>
                    <div class="col-6 col-md-3"><div class="bg-white rounded-4 border p-3 h-100"><div class="fw-bold fs-5">{{ score_breakdown.evidence }}/{{ score_breakdown.evidence_max }}</div><small class="text-muted">Profile Evidence</small></div></div>
                </div>
            </div>
        </div>

        <div class="row g-4 mb-4">

            <div class="col-md-6">

                <div class="card border-0 bg-light h-100">

                    <div class="card-body">

                        <h5 class="fw-bold text-success mb-3">
                            Skills You Meet
                        </h5>

                        {% if matched_skills %}

                            <div class="d-flex flex-wrap gap-2">

                                {% for skill in matched_skills %}

                                    <span class="badge bg-success">
                                        {{ skill }}
                                    </span>

                                {% endfor %}

                            </div>

                        {% else %}

                            <p class="text-muted">
                                No matching skills detected.
                            </p>

                        {% endif %}

                    </div>

                </div>

            </div>

            <div class="col-md-6">

                <div class="card border-0 bg-light h-100">

                    <div class="card-body">

                        <h5 class="fw-bold text-danger mb-3">
                            Skills Still Missing
                        </h5>

                        {% if missing_skills %}

                            <div class="d-flex flex-wrap gap-2">

                                {% for skill in missing_skills %}

                                    <span class="badge bg-danger">
                                        {{ skill }}
                                    </span>

                                {% endfor %}

                            </div>

                        {% else %}

                            <p class="text-success">
                                Excellent skill alignment.
                            </p>

                        {% endif %}

                    </div>

                </div>

            </div>

        </div>

        <div class="card border-0 bg-light mb-4">

            <div class="card-body">

                <h5 class="fw-bold mb-3">
                    Match Strength Analysis
                </h5>

                <ul class="mb-0">

                    {% for strength in strengths %}

                        <li class="mb-2">
                            {{ strength }}
                        </li>

                    {% empty %}

                        <li class="text-muted">
                            No strengths detected.
                        </li>

                    {% endfor %}

                </ul>

            </div>

        </div>

        <div class="card border-0 bg-light mb-4">

            <div class="card-body">

                <h5 class="fw-bold mb-3">
                    AI Explanation
                </h5>

                <ul class="mb-0">

                    {% for explanation in explanations %}

                        <li class="mb-2">
                            {{ explanation }}
                        </li>

                    {% empty %}

                        <li class="text-muted">
                            No AI explanations available.
                        </li>

                    {% endfor %}

                </ul>

            </div>

        </div>

        <hr>

        <p>
            <strong>Company:</strong>
            {{ opportunity.employer.company_name }}
        </p>

        <p>
            <strong>Type:</strong>
            {{ opportunity.get_internship_type_display }}
        </p>

        <p>
            <strong>Location:</strong>
            {{ opportunity.location }}
        </p>

        <p>
            <strong>Slots:</strong>
            {{ opportunity.slots_available }}
        </p>

        <p>
            <strong>Deadline:</strong>
            {{ opportunity.deadline }}
        </p>

        <p>
            <strong>Status:</strong>
            {{ opportunity.status }}
        </p>

        <hr>

        <h4 class="fw-bold">
            Description
        </h4>

        <p>
            {{ opportunity.description }}
        </p>

        <h4 class="fw-bold">
            Employer Required Skills
        </h4>

        <p>
            {{ opportunity.required_skills }}
        </p>

        {% if already_applied %}

            <button class="btn btn-secondary" disabled>
                Already Applied
            </button>

            <small class="text-muted d-block mt-1">

                You have already submitted an application
                for this opportunity.

            </small>

        {% else %}

            <a class="btn btn-primary"
               href="{% url 'apply_opportunity' opportunity.id %}">

                Apply Now

            </a>

        {% endif %}

        <a class="btn btn-outline-dark"
           href="{% url 'opportunity_list' %}">

            Back to Opportunities

        </a>

    </div>

</div>

{% endblock %}

'@
$EmployerApplications = @'
{% extends 'base.html' %}

{% block content %}

<style>
.filter-btn{
    border-radius:14px;
}

.candidate-card{
    border:none;
    border-radius:24px;
    box-shadow:0 15px 35px rgba(15,23,42,.08);
    transition:.25s;
}

.candidate-card:hover{
    transform:translateY(-4px);
}

.score-circle{
    width:80px;
    height:80px;
    border-radius:50%;
    display:flex;
    align-items:center;
    justify-content:center;
    font-weight:700;
    font-size:20px;
    color:white;
}

.score-high{
    background:linear-gradient(135deg,#10b981,#22c55e);
}

.score-medium{
    background:linear-gradient(135deg,#f59e0b,#f97316);
}

.score-low{
    background:linear-gradient(135deg,#ef4444,#dc2626);
}

.skill-pill{
    border-radius:50px;
    padding:7px 12px;
    font-size:12px;
    font-weight:600;
    display:inline-block;
    margin:3px;
}

.chat-btn{
    border-radius:10px;
}

.score-breakdown-mini{
    background:#f8fafc;
    border:1px solid #e2e8f0;
    border-radius:18px;
    padding:12px;
}

.score-breakdown-mini .metric{
    background:white;
    border:1px solid #e2e8f0;
    border-radius:12px;
    padding:9px 6px;
    text-align:center;
    height:100%;
}

.score-breakdown-mini .metric strong{
    display:block;
    font-size:14px;
}

.score-breakdown-mini .metric small{
    color:#64748b;
    font-size:10px;
}
</style>

<div class="d-flex justify-content-between align-items-center mb-4">

    <div>
        <h1 class="fw-bold mb-1">
            Candidate Ranking Board
        </h1>

        <small class="text-muted">
            Applicants ranked by the explainable matching engine
        </small>
    </div>

    <span class="badge bg-primary rounded-pill px-4 py-2">
        {{ ranked_applications|length }} Candidates
    </span>

</div>

<div class="mb-4 d-flex gap-2 flex-wrap">

    <a class="btn filter-btn {% if not status_filter %}btn-dark{% else %}btn-outline-dark{% endif %}"
       href="{% url 'employer_applications' %}">
        All
    </a>

    <a class="btn filter-btn {% if status_filter == 'pending' %}btn-secondary{% else %}btn-outline-secondary{% endif %}"
       href="{% url 'employer_applications' %}?status=pending">
        Pending
    </a>

    <a class="btn filter-btn {% if status_filter == 'shortlisted' %}btn-warning{% else %}btn-outline-warning{% endif %}"
       href="{% url 'employer_applications' %}?status=shortlisted">
        Shortlisted
    </a>

    <a class="btn filter-btn {% if status_filter == 'interview_scheduled' %}btn-info{% else %}btn-outline-info{% endif %}"
       href="{% url 'employer_applications' %}?status=interview_scheduled">
        Interview
    </a>

    <a class="btn filter-btn {% if status_filter == 'accepted' %}btn-success{% else %}btn-outline-success{% endif %}"
       href="{% url 'employer_applications' %}?status=accepted">
        Accepted
    </a>

    <a class="btn filter-btn {% if status_filter == 'rejected' %}btn-danger{% else %}btn-outline-danger{% endif %}"
       href="{% url 'employer_applications' %}?status=rejected">
        Rejected
    </a>

</div>

<div class="row g-4">

{% for item in ranked_applications %}

<div class="col-xl-6">

    <div class="card candidate-card">

        <div class="card-body p-4">

            <div class="d-flex justify-content-between align-items-start mb-4">

                <div>

                    <span class="badge bg-dark mb-2">
                        Rank #{{ forloop.counter }}
                    </span>

                    <h4 class="fw-bold mb-1">
                        {{ item.application.student.full_name }}
                    </h4>

                    <p class="text-muted mb-1">
                        {{ item.application.student.course }}
                    </p>

                    <small class="text-muted">
                        {{ item.application.student.institution }}
                    </small>

                </div>

                {% if item.score >= 80 %}

                    <div class="score-circle score-high">
                        {{ item.score }}%
                    </div>

                {% elif item.score >= 50 %}

                    <div class="score-circle score-medium">
                        {{ item.score }}%
                    </div>

                {% else %}

                    <div class="score-circle score-low">
                        {{ item.score }}%
                    </div>

                {% endif %}

            </div>

            <div class="score-breakdown-mini mb-3">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <small class="fw-bold text-uppercase text-muted">Score Breakdown</small>
                    {% if item.match_level == 'excellent' %}
                        <span class="badge bg-success">Excellent</span>
                    {% elif item.match_level == 'strong' %}
                        <span class="badge bg-primary">Strong</span>
                    {% elif item.match_level == 'moderate' %}
                        <span class="badge bg-warning text-dark">Moderate</span>
                    {% else %}
                        <span class="badge bg-secondary">Low</span>
                    {% endif %}
                </div>
                <div class="row g-2">
                    <div class="col-3"><div class="metric"><strong>{{ item.score_breakdown.skills }}/{{ item.score_breakdown.skills_max }}</strong><small>Skills</small></div></div>
                    <div class="col-3"><div class="metric"><strong>{{ item.score_breakdown.course }}/{{ item.score_breakdown.course_max }}</strong><small>Course</small></div></div>
                    <div class="col-3"><div class="metric"><strong>{{ item.score_breakdown.location }}/{{ item.score_breakdown.location_max }}</strong><small>Location</small></div></div>
                    <div class="col-3"><div class="metric"><strong>{{ item.score_breakdown.evidence }}/{{ item.score_breakdown.evidence_max }}</strong><small>Evidence</small></div></div>
                </div>
            </div>

            <div class="mb-3">

                <strong>Opportunity:</strong>
                {{ item.application.opportunity.title }}

            </div>

            <div class="mb-3">

                <strong>Status:</strong>

                {% if item.application.status == 'accepted' %}

                    <span class="badge bg-success">
                        Accepted
                    </span>

                {% elif item.application.status == 'rejected' %}

                    <span class="badge bg-danger">
                        Rejected
                    </span>

                {% elif item.application.status == 'shortlisted' %}

                    <span class="badge bg-warning text-dark">
                        Shortlisted
                    </span>

                {% elif item.application.status == 'interview_scheduled' %}

                    <span class="badge bg-info text-dark">
                        Interview Scheduled
                    </span>

                {% elif item.application.status == 'reviewed' %}

                    <span class="badge bg-primary">
                        Reviewed
                    </span>

                {% else %}

                    <span class="badge bg-secondary">
                        Pending
                    </span>

                {% endif %}

            </div>

            <hr>

            <div class="mb-3">

                <strong>Matched Skills</strong>

                <div class="mt-2">

                    {% for skill in item.matched_skills %}

                        <span class="skill-pill bg-success text-white">
                            {{ skill }}
                        </span>

                    {% empty %}

                        <span class="text-muted">
                            No matched skills detected.
                        </span>

                    {% endfor %}

                </div>

            </div>

            <div class="mb-3">

                <strong>Missing Skills</strong>

                <div class="mt-2">

                    {% for skill in item.missing_skills %}

                        <span class="skill-pill bg-danger text-white">
                            {{ skill }}
                        </span>

                    {% empty %}

                        <span class="text-success">
                            No major skill gaps detected.
                        </span>

                    {% endfor %}

                </div>

            </div>

            <div class="alert alert-light border mb-4">

                {% if item.score >= 80 %}

                    <strong>Match Recommendation:</strong>
                    Strong candidate. Recommended for interview or direct shortlisting.

                {% elif item.score >= 50 %}

                    <strong>Match Recommendation:</strong>
                    Moderate fit. Review profile and CV before decision.

                {% else %}

                    <strong>Match Recommendation:</strong>
                    Weak fit. Candidate may need further skills alignment.

                {% endif %}

            </div>

            <div class="d-flex gap-2 flex-wrap">

                <a class="btn btn-outline-dark"
                   href="{% url 'application_detail' item.application.id %}">
                    View Profile
                </a>

                <a class="btn btn-outline-primary chat-btn"
                   href="{% url 'application_chat' item.application.id %}">
                    <i class="bi bi-chat-dots-fill"></i>
                    Chat Box
                </a>

                <a class="btn btn-warning"
                   href="{% url 'update_application_status' item.application.id 'shortlisted' %}">
                    Shortlist
                </a>

                <a class="btn btn-info"
                   href="{% url 'schedule_interview' item.application.id %}">
                    Schedule Interview
                </a>

                <a class="btn btn-success"
                   href="{% url 'update_application_status' item.application.id 'accepted' %}">
                    Accept
                </a>

                <a class="btn btn-danger"
                   href="{% url 'update_application_status' item.application.id 'rejected' %}">
                    Reject
                </a>

            </div>

        </div>

    </div>

</div>

{% empty %}

<div class="col-12">

    <div class="alert alert-info">
        No applications found.
    </div>

</div>

{% endfor %}

</div>

{% endblock %}
'@
$ApplicationDetail = @'
{% extends 'base.html' %}

{% block content %}

<style>
.profile-hero{
    background:linear-gradient(135deg,#0f172a,#2563eb);
    color:white;
    border-radius:30px;
    padding:35px;
    margin-bottom:30px;
}

.profile-card{
    border:none;
    border-radius:28px;
    box-shadow:0 15px 35px rgba(15,23,42,.08);
}

.skill-badge{
    padding:10px 16px;
    border-radius:50px;
    font-size:13px;
    font-weight:600;
    display:inline-block;
    margin:4px;
}

.match-badge{
    background:#dcfce7;
    color:#166534;
}

.missing-badge{
    background:#fee2e2;
    color:#991b1b;
}

.avatar{
    width:90px;
    height:90px;
    border-radius:50%;
    object-fit:cover;
    border:4px solid rgba(255,255,255,.3);
}

.info-label{
    font-size:13px;
    color:#64748b;
    font-weight:700;
    text-transform:uppercase;
}

.timeline-box{
    border-left:4px solid #2563eb;
    padding-left:18px;
}

.score-breakdown-card{
    border:none;
    border-radius:28px;
    box-shadow:0 15px 35px rgba(15,23,42,.08);
}

.score-metric{
    border:1px solid #e2e8f0;
    border-radius:18px;
    padding:16px 10px;
    text-align:center;
    height:100%;
}

.score-metric strong{
    display:block;
    font-size:22px;
    color:#0f172a;
}
</style>

<div class="profile-hero">

    <div class="row align-items-center">

        <div class="col-md-8">

            <div class="d-flex align-items-center gap-4">

                {% if application.student.profile_picture %}
                    <img src="{{ application.student.profile_picture.url }}"
                         class="avatar">
                {% else %}
                    <div class="avatar d-flex align-items-center justify-content-center bg-white text-dark fw-bold">
                        {{ application.student.full_name|slice:":1" }}
                    </div>
                {% endif %}

                <div>

                    <h2 class="fw-bold mb-1">
                        {{ application.student.full_name }}
                    </h2>

                    <p class="mb-1 text-white-50">
                        {{ application.student.course }}
                    </p>

                    <p class="mb-0 text-white-50">
                        {{ application.student.institution }}
                    </p>

                </div>

            </div>

        </div>

        <div class="col-md-4 text-md-end mt-4 mt-md-0">

            <h1 class="fw-bold">
                {{ score }}%
            </h1>

            <span class="badge bg-light text-dark">
                Smart Match Score
            </span>

        </div>

    </div>

</div>

<div class="card score-breakdown-card mb-4">
    <div class="card-body p-4">
        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-4">
            <div>
                <h4 class="fw-bold mb-1">Match Score Breakdown</h4>
                <small class="text-muted">Transparent scoring based on requirements and candidate profile evidence.</small>
            </div>
            {% if match_level == 'excellent' %}
                <span class="badge bg-success px-3 py-2">Excellent Match</span>
            {% elif match_level == 'strong' %}
                <span class="badge bg-primary px-3 py-2">Strong Match</span>
            {% elif match_level == 'moderate' %}
                <span class="badge bg-warning text-dark px-3 py-2">Moderate Match</span>
            {% else %}
                <span class="badge bg-secondary px-3 py-2">Low Match</span>
            {% endif %}
        </div>
        <div class="row g-3">
            <div class="col-6 col-lg-3"><div class="score-metric"><strong>{{ score_breakdown.skills }}/{{ score_breakdown.skills_max }}</strong><small class="text-muted">Required Skills</small></div></div>
            <div class="col-6 col-lg-3"><div class="score-metric"><strong>{{ score_breakdown.course }}/{{ score_breakdown.course_max }}</strong><small class="text-muted">Course Relevance</small></div></div>
            <div class="col-6 col-lg-3"><div class="score-metric"><strong>{{ score_breakdown.location }}/{{ score_breakdown.location_max }}</strong><small class="text-muted">Location</small></div></div>
            <div class="col-6 col-lg-3"><div class="score-metric"><strong>{{ score_breakdown.evidence }}/{{ score_breakdown.evidence_max }}</strong><small class="text-muted">Profile Evidence</small></div></div>
        </div>
    </div>
</div>

<div class="row g-4">

    <div class="col-lg-8">

        <div class="card profile-card mb-4">

            <div class="card-body p-4">

                <h4 class="fw-bold mb-4">
                    Candidate Information
                </h4>

                <div class="row">

                    <div class="col-md-6 mb-3">
                        <div class="info-label">Phone</div>
                        <p>{{ application.student.phone_number }}</p>
                    </div>

                    <div class="col-md-6 mb-3">
                        <div class="info-label">Location</div>
                        <p>{{ application.student.location }}</p>
                    </div>

                    <div class="col-md-6 mb-3">
                        <div class="info-label">Institution</div>
                        <p>{{ application.student.institution }}</p>
                    </div>

                    <div class="col-md-6 mb-3">
                        <div class="info-label">Course</div>
                        <p>{{ application.student.course }}</p>
                    </div>

                    <div class="col-md-12">
                        <div class="info-label">Bio</div>
                        <p>{{ application.student.bio }}</p>
                    </div>

                </div>

            </div>

        </div>

        <div class="card profile-card mb-4">

            <div class="card-body p-4">

                <h4 class="fw-bold mb-4">
                    Academic Qualifications
                </h4>

                {% for item in academic_qualifications %}

                    <div class="timeline-box mb-4">

                        <h5 class="fw-bold mb-1">
                            {{ item.qualification }}
                        </h5>

                        <p class="mb-1">
                            {{ item.institution_name }}
                        </p>

                        <p class="mb-1 text-muted">
                            {{ item.course_name }}
                        </p>

                        <small class="text-muted">
                            {{ item.start_year }} - {{ item.end_year }}
                        </small>

                        {% if item.grade %}
                            <br>
                            <span class="badge bg-success mt-2">
                                Grade: {{ item.grade }}
                            </span>
                        {% endif %}

                    </div>

                {% empty %}

                    <p class="text-muted">
                        No academic qualifications added.
                    </p>

                {% endfor %}

            </div>

        </div>

        <div class="card profile-card mb-4">

            <div class="card-body p-4">

                <h4 class="fw-bold mb-4">
                    Work Experience
                </h4>

                {% for item in work_experiences %}

                    <div class="timeline-box mb-4">

                        <h5 class="fw-bold mb-1">
                            {{ item.position }}
                        </h5>

                        <p class="mb-1">
                            {{ item.organization }}
                        </p>

                        <small class="text-muted">
                            {{ item.start_date }} - {{ item.end_date }}
                        </small>

                        {% if item.responsibilities %}
                            <p class="mt-3 mb-0">
                                {{ item.responsibilities }}
                            </p>
                        {% endif %}

                    </div>

                {% empty %}

                    <p class="text-muted">
                        No work experience added.
                    </p>

                {% endfor %}

            </div>

        </div>

        <div class="card profile-card mb-4">

            <div class="card-body p-4">

                <h4 class="fw-bold mb-4">
                    Matched Skills
                </h4>

                {% for skill in matched_skills %}

                    <span class="skill-badge match-badge">
                        {{ skill }}
                    </span>

                {% empty %}

                    <p class="text-muted">
                        No matched skills detected.
                    </p>

                {% endfor %}

            </div>

        </div>

        <div class="card profile-card mb-4">

            <div class="card-body p-4">

                <h4 class="fw-bold mb-4">
                    Missing Skills
                </h4>

                {% for skill in missing_skills %}

                    <span class="skill-badge missing-badge">
                        {{ skill }}
                    </span>

                {% empty %}

                    <p class="text-success">
                        No missing skills detected.
                    </p>

                {% endfor %}

            </div>

        </div>

        <div class="card profile-card mb-4">

            <div class="card-body p-4">

                <h4 class="fw-bold mb-4">
                    Match Analysis
                </h4>

                <ul>

                    {% for explanation in explanations %}
                        <li>{{ explanation }}</li>
                    {% empty %}
                        <li>No match explanation available.</li>
                    {% endfor %}

                </ul>

            </div>

        </div>

        <div class="card profile-card">

            <div class="card-body p-4">

                <h4 class="fw-bold mb-4">
                    Referees
                </h4>

                {% for item in referees %}

                    <div class="border rounded p-3 mb-3">

                        <h5 class="fw-bold mb-1">
                            {{ item.full_name }}
                        </h5>

                        <p class="mb-1">
                            {{ item.position }}
                        </p>

                        <p class="mb-1">
                            {{ item.organization }}
                        </p>

                        <p class="mb-1">
                            {{ item.phone_number }}
                        </p>

                        <p class="mb-0">
                            {{ item.email }}
                        </p>

                    </div>

                {% empty %}

                    <p class="text-muted">
                        No referees added.
                    </p>

                {% endfor %}

            </div>

        </div>

    </div>

    <div class="col-lg-4">

        <div class="card profile-card mb-4">

            <div class="card-body p-4">

                <h4 class="fw-bold mb-3">
                    Candidate Assets
                </h4>

                {% if application.student.github %}
                    <a href="{{ application.student.github }}"
                       target="_blank"
                       class="btn btn-dark w-100 mb-2">
                        GitHub
                    </a>
                {% endif %}

                {% if application.student.linkedin %}
                    <a href="{{ application.student.linkedin }}"
                       target="_blank"
                       class="btn btn-primary w-100 mb-2">
                        LinkedIn
                    </a>
                {% endif %}

                {% if application.student.portfolio %}
                    <a href="{{ application.student.portfolio }}"
                       target="_blank"
                       class="btn btn-success w-100 mb-2">
                        Portfolio
                    </a>
                {% endif %}

                {% if application.student.cv %}
                    <a href="{{ application.student.cv.url }}"
                       target="_blank"
                       class="btn btn-outline-dark w-100">
                        View CV
                    </a>
                    <a href="{% url 'generate_resume_pdf' %}"
   target="_blank"
   class="btn btn-danger w-100 mt-2">
    Download Resume PDF
</a>
                {% endif %}

            </div>

        </div>

        <div class="card profile-card mb-4">

            <div class="card-body p-4">

                <h4 class="fw-bold mb-3">
                    Application Status
                </h4>

                <p>
                    <strong>Opportunity:</strong><br>
                    {{ application.opportunity.title }}
                </p>

                <p>
                    <strong>Status:</strong><br>

                    {% if application.status == 'accepted' %}
                        <span class="badge bg-success">Accepted</span>
                    {% elif application.status == 'rejected' %}
                        <span class="badge bg-danger">Rejected</span>
                    {% elif application.status == 'shortlisted' %}
                        <span class="badge bg-warning text-dark">Shortlisted</span>
                    {% elif application.status == 'interview_scheduled' %}
                        <span class="badge bg-info text-dark">Interview Scheduled</span>
                    {% else %}
                        <span class="badge bg-secondary">Pending</span>
                    {% endif %}
                </p>

                <p>
                    <strong>Applied At:</strong><br>
                    {{ application.applied_at }}
                </p>

            </div>

        </div>

        {% if application.interview_date %}

        <div class="card profile-card mb-4">

            <div class="card-body p-4">

                <h4 class="fw-bold mb-3">
                    Interview Details
                </h4>

                <p><strong>Date:</strong> {{ application.interview_date }}</p>
                <p><strong>Time:</strong> {{ application.interview_time }}</p>
                <p><strong>Venue:</strong> {{ application.interview_location }}</p>

                <p>
                    <strong>Student Response:</strong><br>

                    {% if application.interview_response == 'accepted' %}
                        <span class="badge bg-success">Accepted Interview</span>
                    {% elif application.interview_response == 'declined' %}
                        <span class="badge bg-danger">Declined Interview</span>
                    {% else %}
                        <span class="badge bg-warning text-dark">Pending Response</span>
                    {% endif %}
                </p>

                {% if application.interview_notes %}
                    <p><strong>Notes:</strong> {{ application.interview_notes }}</p>
                {% endif %}

            </div>

        </div>

        {% endif %}

        <div class="d-grid gap-2">

            <a class="btn btn-warning"
               href="{% url 'update_application_status' application.id 'shortlisted' %}">
                Shortlist
            </a>

            <a class="btn btn-primary"
               href="{% url 'schedule_interview' application.id %}">
                Schedule Interview
            </a>

            <a class="btn btn-success"
               href="{% url 'update_application_status' application.id 'accepted' %}">
                Accept
            </a>

            <a class="btn btn-danger"
               href="{% url 'update_application_status' application.id 'rejected' %}">
                Reject
            </a>

            <a class="btn btn-outline-dark"
               href="{% url 'employer_applications' %}">
                Back
            </a>

        </div>

    </div>

</div>

{% endblock %}
'@

$utf8 = New-Object System.Text.UTF8Encoding($false)

[System.IO.File]::WriteAllText(
    (Join-Path (Get-Location) "templates\internships\opportunity_list.html"),
    $OpportunityList,
    $utf8
)
[System.IO.File]::WriteAllText(
    (Join-Path (Get-Location) "templates\internships\opportunity_detail.html"),
    $OpportunityDetail,
    $utf8
)
[System.IO.File]::WriteAllText(
    (Join-Path (Get-Location) "templates\internships\employer_applications.html"),
    $EmployerApplications,
    $utf8
)
[System.IO.File]::WriteAllText(
    (Join-Path (Get-Location) "templates\internships\application_detail.html"),
    $ApplicationDetail,
    $utf8
)

$patch = @'
from pathlib import Path

path = Path("internships/views.py")
text = path.read_text(encoding="utf-8")

def section(name, next_name):
    start = text.find(f"def {name}")
    if start == -1:
        raise SystemExit(f"Could not find function: {name}")
    end = text.find(f"def {next_name}", start)
    if end == -1:
        raise SystemExit(f"Could not find next function: {next_name}")
    return start, end

# opportunity_detail
s, e = section("opportunity_detail", "apply_opportunity")
part = text[s:e]

if "score_breakdown = {}" not in part:
    old = """    strengths = []
    explanations = []

    if student:
"""
    new = """    strengths = []
    explanations = []
    match_level = 'low'
    score_breakdown = {}

    if student:
"""
    if old not in part:
        raise SystemExit("Could not patch opportunity_detail defaults.")
    part = part.replace(old, new, 1)

if "match_level = analysis.get('match_level'" not in part:
    old = """        strengths = analysis.get('strengths', [])
        explanations = analysis.get('explanations', [])
"""
    new = """        strengths = analysis.get('strengths', [])
        explanations = analysis.get('explanations', [])
        match_level = analysis.get('match_level', 'low')
        score_breakdown = analysis.get('score_breakdown', {})
"""
    if old not in part:
        raise SystemExit("Could not patch opportunity_detail analysis.")
    part = part.replace(old, new, 1)

if "'score_breakdown': score_breakdown" not in part:
    old = """            'strengths': strengths,
            'explanations': explanations,
"""
    new = """            'strengths': strengths,
            'explanations': explanations,
            'match_level': match_level,
            'score_breakdown': score_breakdown,
"""
    if old not in part:
        raise SystemExit("Could not patch opportunity_detail context.")
    part = part.replace(old, new, 1)

text = text[:s] + part + text[e:]

# employer_applications
s, e = section("employer_applications", "application_detail")
part = text[s:e]
if "'score_breakdown': analysis.get('score_breakdown'" not in part:
    old = """            'matched_skills': analysis.get('matched_skills', []),
            'missing_skills': analysis.get('missing_skills', []),
        })
"""
    new = """            'matched_skills': analysis.get('matched_skills', []),
            'missing_skills': analysis.get('missing_skills', []),
            'match_level': analysis.get('match_level', 'low'),
            'score_breakdown': analysis.get('score_breakdown', {}),
        })
"""
    if old not in part:
        raise SystemExit("Could not patch employer_applications.")
    part = part.replace(old, new, 1)
text = text[:s] + part + text[e:]

# application_detail
s, e = section("application_detail", "update_application_status")
part = text[s:e]
if "'score_breakdown': analysis.get('score_breakdown'" not in part:
    old = """            'strengths': analysis.get('strengths', []),
            'explanations': analysis.get('explanations', []),
"""
    new = """            'strengths': analysis.get('strengths', []),
            'explanations': analysis.get('explanations', []),
            'match_level': analysis.get('match_level', 'low'),
            'score_breakdown': analysis.get('score_breakdown', {}),
"""
    if old not in part:
        raise SystemExit("Could not patch application_detail.")
    part = part.replace(old, new, 1)
text = text[:s] + part + text[e:]

path.write_text(text, encoding="utf-8")
print("Step 5B view wiring installed.")
'@

$patch | python -

Write-Host ""
Write-Host "Step 5B installed successfully." -ForegroundColor Green
Write-Host "Backup created in .\step5b_backup" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Now run:" -ForegroundColor Cyan
Write-Host "  python manage.py check"
Write-Host "  python manage.py test matching"
