
ROLE_COURSE_CATALOG = {
    "AI_Engineer": {
        "Docker": {
            "title": "Containerization of ML Inference Microservices",
            "provider": "NPTEL / IIT Kharagpur ? 16 Hours",
            "capstone": "Multi-stage Docker builds for FastAPI models, optimizing image size under 120MB",
            "difficulty": "Intermediate",
            "boost": "+8.5% Readiness Boost",
            "url": "https://nptel.ac.in"
        },
        "MLOps": {
            "title": "Machine Learning in Production & Drift Tracking",
            "provider": "DeepLearning.AI / Coursera ? 24 Hours",
            "capstone": "Deploy MLflow Tracking Server with artifact registry and automated drift trigger",
            "difficulty": "Advanced",
            "boost": "+11.0% Readiness Boost",
            "url": "https://coursera.org"
        },
        "PyTorch": {
            "title": "Modular ResNet Backprop Pipelines on CUDA",
            "provider": "Coursera / IBM Skills ? 20 Hours",
            "capstone": "Construct and train modular ResNet backprop pipeline without high-level wrappers",
            "difficulty": "Advanced",
            "boost": "+12.5% Readiness Boost",
            "url": "https://coursera.org"
        }
    },
    "Backend_Systems": {
        "Database/SQL": {
            "title": "PostgreSQL High-Concurrency & Indexing Tuning",
            "provider": "SWAYAM / NPTEL ? 18 Hours",
            "capstone": "Design ACID-compliant multi-tenant schema with connection pooling & query optimization",
            "difficulty": "Advanced",
            "boost": "+14.0% Readiness Boost",
            "url": "https://swayam.gov.in"
        },
        "Docker": {
            "title": "Microservices Orchestration & Docker Compose",
            "provider": "Docker Curriculum ? 12 Hours",
            "capstone": "Build multi-container network with Redis caching, async workers, and Nginx reverse proxy",
            "difficulty": "Intermediate",
            "boost": "+9.5% Readiness Boost",
            "url": "https://docker-curriculum.com"
        },
        "FastAPI": {
            "title": "Production Async Microservices with Asyncpg",
            "provider": "TestDriven.io ? 14 Hours",
            "capstone": "Develop async REST engine with schema validation, rate-limiting, and JWT auth",
            "difficulty": "Intermediate",
            "boost": "+10.0% Readiness Boost",
            "url": "https://testdriven.io"
        }
    },
    "Full_Stack": {
        "Frontend/React": {
            "title": "Modern Reactive Web Applications & State Architecture",
            "provider": "freeCodeCamp / FullStackOpen ? 25 Hours",
            "capstone": "Build real-time websocket client dashboard synced with background workers",
            "difficulty": "Intermediate",
            "boost": "+10.5% Readiness Boost",
            "url": "https://fullstackopen.com"
        },
        "Database/SQL": {
            "title": "Relational Data Modeling & REST Integration",
            "provider": "NPTEL / IIT Madras ? 20 Hours",
            "capstone": "Implement relational schemas with foreign key DAG cascading and migrations",
            "difficulty": "Intermediate",
            "boost": "+8.0% Readiness Boost",
            "url": "https://nptel.ac.in"
        }
    }
}

from fastapi import FastAPI, UploadFile, File, Form, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import re
from typing import Dict, List, Any

from backend.github_scanner import scanner
from backend.scoring import scoring

app = FastAPI(title="TalentOS Bharat Engine", version="3.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LIVE_CANDIDATE_REGISTRY: List[Dict[str, Any]] = []

class CourseRequest(BaseModel):
    skills: Dict[str, float]

@app.get("/")
def serve_index():
    return FileResponse("frontend/index.html")

def extract_real_skills_from_text(text: str) -> Dict[str, float]:
    lower_text = text.lower()
    skill_patterns = {
        "Python": [r"\bpython\b", r"\bpy\b"],
        "FastAPI": [r"\bfastapi\b", r"\buvicorn\b", r"\bpydantic\b"],
        "Machine Learning": [r"\bmachine learning\b", r"\bscikit-learn\b", r"\bsklearn\b"],
        "Deep Learning": [r"\bdeep learning\b", r"\bneural network\b", r"\bcnn\b"],
        "PyTorch": [r"\bpytorch\b", r"\btorch\b"],
        "Docker": [r"\bdocker\b", r"\bcontainer\b", r"\bdockerfile\b"],
        "MLOps": [r"\bmlops\b", r"\bmlflow\b", r"\bkubeflow\b"],
        "Database/SQL": [r"\bsql\b", r"\bpostgres\b", r"\bsqlalchemy\b", r"\bmysql\b"]
    }
    extracted = {}
    for skill, patterns in skill_patterns.items():
        count = sum(len(re.findall(p, lower_text)) for p in patterns)
        if count > 0:
            extracted[skill] = min(0.90, round(0.40 + (count * 0.15), 2))
        else:
            extracted[skill] = 0.0
    return extracted

@app.post("/api/candidate/audit-full")
async def audit_full(
    resume_file: UploadFile = File(...),
    github_url: str = Form(...),
    target_role: str = Form("AI_Engineer"),
    candidate_name: str = Form("Suyash Sharma")
):
    raw_bytes = await resume_file.read()
    resume_text = raw_bytes.decode("utf-8", errors="ignore")
    detected_claims = extract_real_skills_from_text(resume_text)
    code_evidence = scanner.scan_repository(github_url)
    audit_summary = scoring.calculate_grounded_score(detected_claims, code_evidence, target_role)

    candidate_record = {
        "uid": f"CAN-{len(LIVE_CANDIDATE_REGISTRY)+101}",
        "name": candidate_name,
        "github": github_url,
        "role": target_role.replace("_", " "),
        "capability_score": audit_summary["readiness_score"],
        "evidence_density": "High (Behavioral AST Verified)" if audit_summary["verified_skills_count"] >= 2 else "Low (Zero Artifacts)",
        "core_stack": [s for s, v in detected_claims.items() if v > 0.3][:4],
        "verification_status": "Graph + ML Verified" if "Verified" in audit_summary["penalty_status"] else "Penalty Enforced (-50%)",
        "status_badge": "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" if "Verified" in audit_summary["penalty_status"] else "bg-rose-500/10 text-rose-400 border-rose-500/30",
        "raw_claims": detected_claims
    }

    existing_idx = next((i for i, c in enumerate(LIVE_CANDIDATE_REGISTRY) if c["name"] == candidate_name), None)
    if existing_idx is not None:
        LIVE_CANDIDATE_REGISTRY[existing_idx] = candidate_record
    else:
        LIVE_CANDIDATE_REGISTRY.append(candidate_record)

    return {
        "candidate_uid": candidate_record["uid"],
        "candidate_name": candidate_name,
        "github_scanned": code_evidence.get("repo", "live-repo"),
        "detected_claims": detected_claims,
        "readiness_summary": audit_summary,
        "live_registry_count": len(LIVE_CANDIDATE_REGISTRY)
    }

@app.get("/api/recruiter/talent-pool")
def get_recruiter_pool(role: str = "AI Engineer"):
    if not LIVE_CANDIDATE_REGISTRY:
        return []
    filtered = [c for c in LIVE_CANDIDATE_REGISTRY if c["role"] == role or role == "All"]
    filtered.sort(key=lambda x: x["capability_score"], reverse=True)
    return filtered


@app.post("/api/candidate/recommended-courses")
def get_recommended_courses(req: dict = None):
    req_data = req or {}
    role = req_data.get("target_role", "AI_Engineer").replace(" ", "_")
    skills = req_data.get("skills", {})
    
    catalog = ROLE_COURSE_CATALOG.get(role, ROLE_COURSE_CATALOG["AI_Engineer"])
    recommendations = []
    
    for skill, cat in catalog.items():
        score = skills.get(skill, 0.0)
        if score < 0.7:
            recommendations.append({
                "deficit_skill": skill,
                "deficit_label": f"Role Deficit: {skill}",
                "course_title": cat["title"],
                "provider_info": cat["provider"],
                "capstone_title": cat["capstone"],
                "difficulty": cat["difficulty"],
                "readiness_boost": cat["boost"],
                "module_url": cat["url"]
            })
            
    if not recommendations:
        for skill, cat in list(catalog.items())[:2]:
            recommendations.append({
                "deficit_skill": skill,
                "deficit_label": f"Target Benchmark: {skill}",
                "course_title": cat["title"],
                "provider_info": cat["provider"],
                "capstone_title": cat["capstone"],
                "difficulty": cat["difficulty"],
                "readiness_boost": cat["boost"],
                "module_url": cat["url"]
            })
            
    return recommendations

@app.get("/api/university/cohort-metrics")
def get_cohort_metrics():
    total = len(LIVE_CANDIDATE_REGISTRY)
    if total == 0:
        return {
            "total_students": 0,
            "average_readiness": 0.0,
            "deficits": {
                "MLOps & Tracking": {"percentage": 0, "impact": "None"},
                "Docker & Containerization": {"percentage": 0, "impact": "None"}
            }
        }
    avg_score = round(sum(c["capability_score"] for c in LIVE_CANDIDATE_REGISTRY) / total, 1)
    mlops_lacking = sum(1 for c in LIVE_CANDIDATE_REGISTRY if c["raw_claims"].get("MLOps", 0.0) < 0.40)
    docker_lacking = sum(1 for c in LIVE_CANDIDATE_REGISTRY if c["raw_claims"].get("Docker", 0.0) < 0.40)
    return {
        "total_students": total,
        "average_readiness": avg_score,
        "deficits": {
            "MLOps & Tracking": {"percentage": round((mlops_lacking / total) * 100), "impact": "Critical"},
            "Docker & Containerization": {"percentage": round((docker_lacking / total) * 100), "impact": "High"}
        }
    }

@app.get("/api/university/export-syllabus-patch")
def export_syllabus_patch():
    patch_data = {
        "institution_program": "B.E. Computer Science & Engineering (Batch 2026)",
        "accreditation_compliance": "NEP 2020 Vocational Credit Framework (2 Credits)",
        "cohort_size_audited": len(LIVE_CANDIDATE_REGISTRY),
        "curriculum_patch_modules": [
            {"week": "Weeks 1 - 2 (16 Hours)", "topic": "Containerization of ML Inference Microservices", "lab_objective": "Multi-stage Docker builds for FastAPI models"},
            {"week": "Weeks 3 - 4 (16 Hours)", "topic": "Experiment Tracking & Registry with MLflow", "lab_objective": "Continuous metric logging and artifact versioning"},
            {"week": "Week 5 (8 Hours)", "topic": "Automated Cloud Deployment via GitHub Actions", "lab_objective": "CI/CD testing and registry push"}
        ]
    }
    return Response(
        content=json.dumps(patch_data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=NEP2020_40Hr_Curriculum_Patch.json"}
    )