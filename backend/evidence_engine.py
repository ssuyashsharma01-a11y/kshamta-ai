import io
import re
from pypdf import PdfReader

class EvidenceEngine:
    def __init__(self):
        self.evidence_signatures = {
            "Python": {
                "claims": [r"\bpython\b", r"\bpy\b"],
                "evidence": [r"def\s+", r"class\s+", r"lambda", r"pandas", r"numpy", r"pip\b"]
            },
            "Machine Learning": {
                "claims": [r"machine learning", r"scikit-learn", r"sklearn"],
                "evidence": [r"accuracy", r"rmse", r"cross-validation", r"random forest", r"hyperparameter", r"regression"]
            },
            "Deep Learning": {
                "claims": [r"deep learning", r"neural network"],
                "evidence": [r"epochs", r"loss", r"backprop", r"conv2d", r"weights", r"cuda", r"gpu"]
            },
            "PyTorch": {
                "claims": [r"pytorch", r"torch"],
                "evidence": [r"nn\.module", r"torch\.tensor", r"dataloader", r"adam", r"criterion"]
            },
            "FastAPI": {
                "claims": [r"fastapi"],
                "evidence": [r"uvicorn", r"pydantic", r"@app\.", r"swagger", r"async def", r"endpoints"]
            },
            "Docker": {
                "claims": [r"\bdocker\b", r"containerize"],
                "evidence": [r"dockerfile", r"docker-compose", r"entrypoint", r"port mapping"]
            },
            "MLOps": {
                "claims": [r"\bmlops\b"],
                "evidence": [r"mlflow", r"dvc", r"model registry", r"drift detection"]
            },
            "Cloud/AWS": {
                "claims": [r"\baws\b", r"\bcloud\b"],
                "evidence": [r"ec2", r"s3", r"lambda", r"iam", r"ecs", r"cloudwatch"]
            }
        }

    def parse_pdf_bytes(self, pdf_bytes: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            extracted = []
            for page in reader.pages:
                txt = page.extract_text()
                if txt:
                    extracted.append(txt)
            return " ".join(extracted).lower()
        except Exception:
            return ""

    def analyze_profile(self, text: str):
        detected_skills = {}

        for skill, sig in self.evidence_signatures.items():
            claim_hits = sum(len(re.findall(p, text, re.IGNORECASE)) for p in sig["claims"])
            evidence_hits = sum(len(re.findall(p, text, re.IGNORECASE)) for p in sig["evidence"])

            claim_val = min(claim_hits * 0.4, 1.0)
            evidence_val = min(evidence_hits * 0.35, 1.0)

            if claim_hits == 0 and evidence_hits == 0:
                final_score = 0.15
            else:
                final_score = (0.30 * claim_val) + (0.70 * evidence_val)
                if claim_val > 0.4 and evidence_val > 0.4:
                    final_score = min(final_score + 0.15, 0.95)

            detected_skills[skill] = round(final_score, 2)

        return detected_skills
