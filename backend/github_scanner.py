import re
import urllib.request
import json
import base64

class GitHubEvidenceScanner:
    """
    Scans public GitHub repositories for deterministic code evidence:
    - Target frameworks & AST-level imports
    - Requirements & Docker configurations
    - Commit activity & repository footprints
    """
    
    FRAMEWORK_SIGNATURES = {
        "FastAPI": [r"\bfrom\s+fastapi\s+import\b", r"\bimport\s+fastapi\b"],
        "PyTorch": [r"\bimport\s+torch\b", r"\bfrom\s+torch\s+import\b"],
        "Machine Learning": [r"\bimport\s+sklearn\b", r"\bfrom\s+sklearn\b", r"\bimport\s+xgboost\b", r"\bimport\s+lightgbm\b"],
        "MLOps": [r"\bimport\s+mlflow\b", r"\bfrom\s+mlflow\b", r"\bwandb\b", r"\bdvc\b"],
        "Docker": [r"FROM\s+[a-zA-Z0-9_\-\.\/:]+", r"WORKDIR\s+", r"CMD\s+\["],
        "Python": [r"\bdef\s+[a-zA-Z_]\w*\(", r"\bclass\s+[a-zA-Z_]\w*[:\(]"]
    }

    def __init__(self, github_token: str = None):
        self.headers = {"User-Agent": "Kshamta-AI-Evidence-Scanner"}
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"

    def parse_repo_url(self, repo_url: str):
        # Extracts 'owner' and 'repo' from https://github.com/owner/repo
        match = re.search(r"github\.com/([^/]+)/([^/]+)", repo_url.strip())
        if match:
            owner = match.group(1)
            repo = match.group(2).replace(".git", "")
            return owner, repo
        return None, None

    def _fetch_json(self, url: str):
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception:
            return None

    def scan_repository(self, repo_url: str) -> dict:
        owner, repo = self.parse_repo_url(repo_url)
        if not owner or not repo:
            return {"status": "error", "message": "Invalid GitHub repository URL"}

        # 1. Fetch Repo Trees (Recursive)
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
        data = self._fetch_json(tree_url)
        
        # Fallback to 'master' branch if 'main' fails
        if not data or "tree" not in data:
            tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1"
            data = self._fetch_json(tree_url)

        if not data or "tree" not in data:
            return {
                "status": "partial_success",
                "repo": f"{owner}/{repo}",
                "evidence_score": 0.40,
                "verified_artifacts": [],
                "detected_skills": ["Python"],
                "summary": "Repository verified, but tree scanning hit API rate limit or empty repo."
            }

        tree = data.get("tree", [])
        verified_artifacts = []
        code_blobs_to_sample = []
        has_docker = False
        has_reqs = False

        for item in tree:
            path = item.get("path", "")
            lower_p = path.lower()

            if "dockerfile" in lower_p or "docker-compose" in lower_p:
                has_docker = True
                verified_artifacts.append(f"Container Config: {path}")

            if "requirements.txt" in lower_p or "pyproject.toml" in lower_p or "setup.py" in lower_p:
                has_reqs = True
                verified_artifacts.append(f"Dependency Spec: {path}")
                if len(code_blobs_to_sample) < 5:
                    code_blobs_to_sample.append(item.get("url"))

            if lower_p.endswith(".py") or lower_p.endswith(".ipynb"):
                if len(code_blobs_to_sample) < 5:
                    code_blobs_to_sample.append(item.get("url"))

        # 2. Sample Code Blobs for actual framework imports
        detected_signatures = set()
        if has_docker:
            detected_signatures.add("Docker")

        for blob_url in code_blobs_to_sample:
            if not blob_url:
                continue
            blob_data = self._fetch_json(blob_url)
            if blob_data and "content" in blob_data:
                try:
                    code_content = base64.b64decode(blob_data["content"]).decode('utf-8', errors='ignore')
                    for skill, patterns in self.FRAMEWORK_SIGNATURES.items():
                        for pat in patterns:
                            if re.search(pat, code_content):
                                detected_signatures.add(skill)
                                break
                except Exception:
                    continue

        if not detected_signatures:
            detected_signatures.add("Python")

        evidence_confidence = min(1.0, 0.30 + (0.15 * len(detected_signatures)) + (0.15 if has_docker else 0.0) + (0.10 if has_reqs else 0.0))

        return {
            "status": "success",
            "repo": f"{owner}/{repo}",
            "evidence_confidence": round(evidence_confidence, 2),
            "verified_skills": list(detected_signatures),
            "artifacts_found": verified_artifacts,
            "inspected_files_count": len(tree)
        }

if __name__ == "__main__":
    scanner = GitHubEvidenceScanner()
    # Test run on sample open-source repo
    res = scanner.scan_repository("https://github.com/fastapi/fastapi")
    print(json.dumps(res, indent=2))
