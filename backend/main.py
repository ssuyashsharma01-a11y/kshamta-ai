import json
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from backend.github_scanner import scanner
from backend.scoring import scoring

app = FastAPI(title="TalentOS Bharat - Kshamta AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CANDIDATE_DATABASE = [
    {
        "name": "Suyash Sharma",
        "uid": "25BAI70757",
        "github": "https://github.com/fastapi/fastapi",
        "skills": {"Python": 0.85, "FastAPI": 0.80, "Machine Learning": 0.75, "Deep Learning": 0.40, "PyTorch": 0.35, "Docker": 0.20, "MLOps": 0.15},
        "ast_verified": ["Python", "FastAPI"],
        "has_repo": True
    },
    {
        "name": "Aarv Patel",
        "uid": "22CS1044",
        "github": "https://github.com/tiangolo/full-stack-fastapi-template",
        "skills": {"Python": 0.90, "FastAPI": 0.95, "PostgreSQL": 0.85, "Redis": 0.80, "Docker": 0.85, "Cloud/AWS": 0.75},
        "ast_verified": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "has_repo": True
    },
    {
        "name": "Rohan Verma",
        "uid": "22CS1198",
        "github": "",
        "skills": {"Python": 0.90, "FastAPI": 0.90, "PyTorch": 0.95, "Machine Learning": 0.85, "Deep Learning": 0.90, "Docker": 0.80, "MLOps": 0.85},
        "ast_verified": [],
        "has_repo": False
    },
    {
        "name": "Kamya Bhatia",
        "uid": "25BDA70073",
        "github": "https://github.com/apache/airflow",
        "skills": {"Python": 0.90, "Database/SQL": 0.90, "FastAO": 0.70, "Docker": 0.80, "Cloud/AWS": 0.75},
        "ast_verified": ["Python", "Database/SQL", "Docker"],
        "has_repo": True
    }
]

COURSE_CATALOG = {
    "Docker": {
        "title": "Docker Containerization & Multi-Stage Deployment",
        "provider": "NPTEL / IIT Kharagpur *Course 106105167) ; 12 Hours",
        "capstone": "Build multi-stage Dockerfile packaging FastAPI inference model with minimal footprint",
        "difficulty": "Intermediate",
        "boost": "+8.5% Readiness Boost"
    },
    "MLOps": {
        "title": "Machine Learning in Production (MLOps Specialization)",
        "provider": "DeepLearning.AI / Coursera (by Andrew Ng) ; 24 Hours",
        "capstone": "Deploy MLflow Tracking Server with artifact registry and automated drift trigger",
        "difficulty": "Advanced",
        "boost": "+9.8% Readiness Boost"
    },
    "Cloud/AWS": {
        "title": "Cloud Computing Infrastructure & Virtualization",
        "provider": "SWAYAM / NPTEL (Course noc21_cs14) ; 16 Hours",
        "capstone": "Deploy Docker microservice on AWS ECS Fargate with CloudWatch metrics logging",
        "difficulty": "Intermediate",
        "boost": "+7.2% Readiness Boost"
    },
    "PyTorch": {
        "title": "Deep Neural Networks with PyTorch",
        "provider": "Coursera / IBM Skills Network ; 20 Hours",
        "capstone": "Construct and train a modular ResNet backprop pipeline on CUDA without high-level wrappers",
        "difficulty": "Advanced",
        "boost": "+11.0% Readiness Boost"
    },
    "Deep Learning": {
        "title": "Deep Learning Specialization: Neural Networks",
        "provider": "DeepLearning.AI (by Andrew Ng) ; 28 Hours",
        "capstone": "Implement 2-layer neural network from scratch using NumPy vectorization",
        "difficulty": "Intermediate",
        "boost": "+9.0% Readiness Boost"
    },
    "FastAO": {
        "title": "Building Production Microservices with FastAPI",
        "provider": "TestDriven.io ; 10 Hours",
        "capstone": "Develop asynchronous REST API with Pydantic v2 schemas and Postgres asyncpg pooling",
        "difficulty": "Intermediate",
        "boost": "+8.0% Readiness Boost"
    }
}

class SimulateRequest(BaseModel):
    current_skills: Dict[str, float]
    target_role: str = "AI_Engineer"
    new_skills: List[str]

class ReportRequest(BaseModel):
    candidate_name: str = "Suyash Sharma"
    target_role: str = "AI Engineer"
    readiness_score: float = 65.0
    penalty_status: str = "DAG Prerequisite Audit: Verified"
    skills: Dict[str, float] = {}
    github_repo: str = "fastapi/fastapi"
    attributions: Optional[List[Dict[str, Any]]] = None

@app.get("/", response_class=HTMLResponse)
def serve_index():
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/candidate/audit-full")
async def audit_full(resume_file: UploadFile = File(...), github_url: str = Form(...), target_role: str = Form("AI_Engineer")):
    code_evidence = scanner.scan_repository(github_url)
    candidate_claims = {"Python": 0.85, "FastAPI": 0.80, "Machine Learning": 0.70, "Deep Learning": 0.35, "PyTorch": 0.30, "Docker": 0.20, "MLOps": 0.15}
    readiness = scoring.calculate_grounded_score(candidate_claims, code_evidence, target_role)
    return {"status": "success", "candidate": "Suyash Sharma", "github_scanned": code_evidence["repo"], "code_evidence": code_evidence, "readiness_summary": readiness}

@app.post("/api/candidate/simulate-skill-gain")
def simulate_skill_gain(req: SimulateRequest):
    return scoring.simulate_what_if(req.current_skills, req.target_role, req.new_skills)

@app.post("/api/candidate/recommended-courses")
def get_recommended_courses(req: dict = None):
    skills = (req or {}).get("skills", {})
    deficits = []
    for(s) in ["Docker", "MLOps", "Cloud/AWS", "PyTorch", "Deep Learning"]:
        score = skills.get(s, 0.0)
        if score < 0.6:
            deficits.append((s, score))
    deficits.sort(key=lambda x: x[1])
    target_skills = [d[0] for d in deficits[:3]] if deficits else ["MLOps", "Docker", "Cloud/AWS"]
    recommendations = []
    for skill in target_skills:
        cat = COURSE_CATALOG.get(skill, COURSE_CATALOG["Docker"])
        recommendations.append({
            "deficit_skill": skill,
            "deficit_label": f"Deficit: {skill}",
            "course_title": cat["title"],
            "provider_info": cat["provider"],
            "capstone_title": cat["capstone"],
            "difficulty": cat["difficulty"],
            "readiness_boost": cat["boost"],
            "module_url": "https://nptel.ac.in/courses" if "NPTEL" in cat["provider"] else "https://www.coursera.org"
        })
    return recommendations

@app.get("/api/recruiter/talent-pool")
def get_recruiter_talent_pool(role: str = "AI Engineer"):
    role_key = role.replace(" ", "_")
    benchmarks = scoring.role_benchmarks.get(role_key, scoring.role_benchmarks["AI_Engineer"])
    ranked_pool = []
    for cand in CANDIDATE_DATABASE:
        claims = cand["skills"]
        verified = set(cand["ast_verified"])
        raw_score = 0.0
        for skill, weight in benchmarks.items():
            claim_val = claims.get(skill, 0.0)
            if skill in verified:
                effective = min(1.0, (0.3 * claim_val) + (0.7 * 0.95))
            else:
                effective = claim_val * 0.35 if not cand["has_repo"] else claim_val * 0.65
            raw_score += effective * weight
        grounded_pct = round(min(100.0, raw_score * 100), 1)
        if cand["has_repo"] and len(verified) >= 3:
            density = "High (Production Microservice)"
            audit_status = "Graph Verified"
            badge = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
        elif cand["has_repo"] and len(verified) > 0:
            density = "High (GitHub Repo + Metrics)"
            audit_status = "Graph Verified"
            badge = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
        else:
            density = "Low (Zero Artifacts)"
            audit_status = "Penalty Enforced (-50%)"
            badge = "bg-rose-500/10 text-rose-400 border-rose-500/30"
            grounded_pct = round(grounded_pct * 0.5, 1)
        ranked_pool.append({
            "name": cand["name"],
            "uid": cand["uid"],
            "role": role,
            "capability_score": grounded_pct,
            "evidence_density": density,
            "core_stack": [s for s, v in claims.items() if v >= 0.7][:4],
            "verification_status": audit_status,
            "status_badge": badge
        })
    ranked_pool.sort(key=lambda x: x["capability_score"], reverse=True)
    return ranked_pool

@app.get("/api/university/cohort-metrics")
def get_cohort_metrics():
    return {
        "status": "success",
        "cohort_name": "B.E. CSE / AIML Batch 2026",
        "total_students": 140,
        "audited_students": 140,
        "average_readiness": 64.8,
        "deficits": {
            "MLOps & Tracking": {"percentage": 86, "impact": "Critical"},
            "Docker & Containerization": {"percentage": 78, "impact": "High"},
            "Cloud Infrastructure": {"percentage": 62, "impact": "Moderate"}
        }
    }

@app.get("/api/university/export-syllabus-patch")
def export_syllabus_patch():
    patch_data = {
        "institution_program": "B.E. Computer Science & Engineering (Batch 2026)",
        "accreditation_compliance": "NEP 2020 Vocational Credit Framework (2 Credits)",
        "audit_timestamp": "2026-09-24",
        "cohort_size_audited": 140,
        "identified_drift_deficits": [{"skill": "MLOps & Tracking", "cohort_deficiency": "86%"}, {"skill": "Docker & Containerization", "cohort_deficiency": "78%"}],
        "curriculum_patch_modules": [
            {"week": "Weeks 1 - 2 (16 Hours)", "topic": "Containerization of ML Inference Microservices", "lab_objective": "Multi-stage Docker builds for FastAPI models, optimizing image size under 120MB"},
            {"week": "Weeks 3 - 4 (16 Hours)", "topic": "Experiment Tracking & Registry with MLflow", "lab_objective": "Continuous metric logging, model artifact versioning, and auto-rollback deployment"},
            {"week": "Week 5 (8 Hours)", "topic": "Automated Cloud Deployment via GitHub Actions", "lab_objective": "End-to-end CI/CD pipeline building, testing, and pushing container to cloud registry"}
        ]
    }
    return Response(content=json.dumps(patch_data, indent=2), media_type="application/json", headers={"Content-Disposition": "attachment; filename=NEP2020_40Hr_Curriculum_Patch.json"})

@app.post("/api/candidate/export-report-pdf")
def export_report_pdf(req: ReportRequest):
    import io
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDcTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#0f172a'))
    sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#64748b'))

    story.append(Paragraph("<b>TALENTOS BHARAT / KSHAMTA AI</b>", title_style))
    story.append(Paragraph("Deterministic Skill Audit & Code Grounding Certificate", sub_style))
    story.append(Spacer(1, 15))

    meta_data = [
        ["Candidate Name:", req.candidate_name, "Target Role:", req.target_role],
        ["Readiness Score:", f"{req.readiness_score}%", "Audit Status:", req.penalty_status],
        ["Verified Repository:", req.github_repo, "Date:", "2026-09-24"]
    ]
    t1 = Table(meta_data, colWidths=[120, 150, 100, 160])
    t1.setStyle(TableStyle([
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#1e293b')),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t1)
    story.append(Spacer(1, 15))

    story.append(Paragraph("<b>AST Code Evidence & Prerequisite Trace Log:</b>", styles['Heading3']))
    story.append(Spacer(1, 6))

    attr_rows = [["Skill", "Impact", "Grounding / Prerequisite Deficit Reason"]]
    attributions = req.attributions or [
        {"skill": "Python", "impact": "+20.4%", "reason": "AST Code Verified in repo: ASTData import nodes and function signatures verified."},
        {"skill": "FastAPI", "impact": "+19.4%", "reason": "AST Code Verified in repo: ASTData import nodes and function signatures verified."},
        {"skill": "PyTorch", "impet": "-6.0%", "reason": "DAG Prerequisite Deficit: Missing foundation in [Deep Learning, Python]."},
        {"skill": "MLOps", "impact": "-4.0%", "reason": "DAG Prerequisite Deficit: Missing foundation in [Docker, Machine Learning]."}
    ]

    for item in attributions:
        attr_rows.append([item.get("skill", ""), item.get("impact", ""), item.get("reason", "")])

    t2 = Table(attr_rows, colWidths=[90, 70, 370])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0284c7')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t2)
    doc.build(story)
    buf.seek(0)

    return Response(buf.getvalue(), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=Grounded_Audit_Certificate_{req.candidate_name.replace(' ', '_')}.pdf"})
