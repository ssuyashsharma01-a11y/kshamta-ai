import os
import pandas as pd
import networkx as nx
from typing import Dict, List, Any
from sklearn.ensemble import RandomForestRegressor

class MathematicalScoringEngine:
    def __init__(self):
        self.dag = nx.DiGraph()
        self._build_skill_dag()

        self.role_benchmarks = {
            "AI_Engineer": {
                "Python": 0.20,
                "Machine Learning": 0.20,
                "Deep Learning": 0.20,
                "PyTorch": 0.15,
                "FastAPI": 0.10,
                "Docker": 0.10,
                "MLOps": 0.05
            },
            "Backend_Developer": {
                "Python": 0.25,
                "FastAPI": 0.30,
                "Database/SQL": 0.20,
                "Docker": 0.15,
                "Cloud/AWS": 0.10
            }
        }

        self.csv_path = os.path.join(os.path.dirname(__file__), "data", "training_data.csv")
        self.rf_model = self._train_random_forest_from_csv()

    def _build_skill_dag(self):
        dependencies = [
            ("Python", "Machine Learning"),
            ("Python", "FastAPI"),
            ("Machine Learning", "Deep Learning"),
            ("Machine Learning", "MLOps"),
            ("Deep Learning", "PyTorch"),
            ("Docker", "MLOps"),
            ("Database/SQL", "FastAPI")
        ]
        self.dag.add_edges_from(dependencies)

    def _train_random_forest_from_csv(self) -> RandomForestRegressor:
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"Training dataset not found at {self.csv_path}")

        df = pd.read_csv(self.csv_path)
        features = ["ast_depth", "dag_fulfillment", "claim_evidence_ratio", "artifact_rigor"]
        target = "job_readiness"

        X = df[features].values
        y = df[target].values

        rf = RandomForestRegressor(n_estimators=50, random_state=42)
        rf.fit(X, y)
        return rf

    def calculate_grounded_score(self, claims: Dict[str, float], code_evidence: Dict[str, Any], target_role: str = "AI_Engineer") -> Dict[str, Any]:
        role_key = target_role.replace(" ", "_")
        weights = self.role_benchmarks.get(role_key, self.role_benchmarks["AI_Engineer"])
        ast_verified = set(code_evidence.get("ast_verified_skills", []))

        attributions = []
        verified_count = 0
        total_prereq_penalties = 0.0

        for skill, weight in weights.items():
            claim_val = claims.get(skill, 0.0)

            # Check DAG dependencies
            ancestors = nx.ancestors(self.dag, skill) if self.dag.has_node(skill) else set()
            missing_prereqs = [anc for anc in ancestors if claims.get(anc, 0.0) < 0.30 or anc not in ast_verified]

            # Trigger prerequisite penalty if claimed without verified foundation
            if missing_prereqs and claim_val > 0.30:
                penalty = min(0.35, len(missing_prereqs) * 0.15)
                total_prereq_penalties += penalty
                attributions.append({
                    "skill": skill,
                    "impact": f"-{round(penalty * 100, 1)}%",
                    "reason": f"DAG Prerequisite Deficit: Claimed without verified foundation in {sorted(list(missing_prereqs))}."
                })
            elif skill in ast_verified and claim_val > 0.0:
                verified_count += 1
                boost = weight * 1.15
                attributions.append({
                    "skill": skill,
                    "impact": f"+{round(boost * 100, 1)}%",
                    "reason": "AST Code Verified: Active behavioral AST calls and decorator nodes confirmed."
                })
            elif claim_val > 0.0:
                attributions.append({
                    "skill": skill,
                    "impact": "-10.0%",
                    "reason": "Unverified Claim: Stated in resume but zero behavioral AST proof in repository."
                })

        # Calculate empirical feature vectors for Random Forest Regressor
        ast_depth_score = min(1.0, (verified_count / max(1, len(ast_verified))) * 0.95) if ast_verified else 0.05
        dag_fulfillment = max(0.05, 1.0 - (total_prereq_penalties / 2.0))
        active_claims = len([v for v in claims.values() if v > 0.1])
        claim_ratio = min(1.0, verified_count / max(1, active_claims)) if active_claims > 0 else 0.05

        # Check for production testing & structure artifacts
        artifacts = code_evidence.get("code_artifacts", [])
        has_tests = any("test" in str(a).lower() for a in artifacts)
        has_docker = any("docker" in str(a).lower() for a in artifacts)
        artifact_flag = 1.0 if (has_tests and has_docker) else (0.5 if artifacts else 0.0)

        features = [[ast_depth_score, dag_fulfillment, claim_ratio, artifact_flag]]
        rf_prediction = float(self.rf_model.predict(features)[0])
        final_readiness_pct = round(min(100.0, rf_prediction * 100), 1)

        feature_importance_map = {
            "AST Behavioral Code Depth": round(float(self.rf_model.feature_importances_[0]), 3),
            "DAG Prerequisite Fulfillment": round(float(self.rf_model.feature_importances_[1]), 3),
            "Claimed-to-Evidence Ratio": round(float(self.rf_model.feature_importances_[2]), 3),
            "Repository Artifact Rigor": round(float(self.rf_model.feature_importances_[3]), 3)
        }

        return {
            "readiness_score": final_readiness_pct,
            "ml_model_used": "Scikit-Learn Random Forest (Trained on training_data.csv)",
            "ml_feature_importances": feature_importance_map,
            "penalty_status": "DAG Prerequisite Audit: Verified" if total_prereq_penalties == 0 else "DAG Prerequisite Deficit Identified",
            "attributions": attributions,
            "verified_skills_count": verified_count,
            "target_role": target_role
        }

ScoringEngine = MathematicalScoringEngine
scoring = MathematicalScoringEngine()
