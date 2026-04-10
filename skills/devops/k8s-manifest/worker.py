# filepath: skills/devops/k8s-manifest/worker.py
import base64, logging
from skillforge.base import BaseWorker, SkillInput, SkillOutput

logger = logging.getLogger(__name__)

class Worker(BaseWorker):
    """Generate Kubernetes manifest YAML files."""
    skill_id = "devops.k8s-manifest"
    version = "1.0.0"

    def run(self, input: SkillInput) -> SkillOutput:
        try:
            app: str = input.data.get("app_name", "")
            image: str = input.data.get("image", "")
            port: int = input.data.get("port", 0)
            if not app or not image or not port:
                return SkillOutput(success=False, error="'app_name', 'image', 'port' required.")

            replicas: int = input.data.get("replicas", 2)
            env_vars: dict = input.data.get("env_vars", {})
            kinds: list = input.data.get("manifests", ["deployment", "service"])
            ns: str = input.data.get("namespace", "default")

            files: dict[str, str] = {}; secrets: list[str] = []

            # Separate secrets
            env_list = []; secret_data = {}
            for k, v in env_vars.items():
                if any(s in k.upper() for s in ("PASSWORD", "SECRET", "KEY", "TOKEN")):
                    secrets.append(k)
                    secret_data[k] = base64.b64encode(v.encode()).decode()
                    env_list.append(f"        - name: {k}\n          valueFrom:\n            secretKeyRef:\n              name: {app}-secret\n              key: {k}")
                else:
                    env_list.append(f"        - name: {k}\n          value: \"{v}\"")
            env_block = "\n".join(env_list)

            if "deployment" in kinds:
                dep = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app}
  namespace: {ns}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {app}
  template:
    metadata:
      labels:
        app: {app}
    spec:
      containers:
      - name: {app}
        image: {image}
        ports:
        - containerPort: {port}
        env:
{env_block}
        readinessProbe:
          httpGet:
            path: /health
            port: {port}
          initialDelaySeconds: 5
        livenessProbe:
          httpGet:
            path: /health
            port: {port}
          initialDelaySeconds: 15"""
                files["deployment.yaml"] = dep

            if "service" in kinds:
                files["service.yaml"] = f"""apiVersion: v1
kind: Service
metadata:
  name: {app}
  namespace: {ns}
spec:
  selector:
    app: {app}
  ports:
  - port: {port}
    targetPort: {port}
  type: ClusterIP"""

            if "secret" in kinds and secret_data:
                data_block = "\n".join(f"  {k}: {v}" for k, v in secret_data.items())
                files["secret.yaml"] = f"apiVersion: v1\nkind: Secret\nmetadata:\n  name: {app}-secret\n  namespace: {ns}\ntype: Opaque\ndata:\n{data_block}"

            combined = "\n---\n".join(files.values())

            return SkillOutput(success=True, data={
                "manifests": files, "combined_yaml": combined,
                "resource_count": len(files), "secrets_detected": secrets,
            }, metadata={"skill_id": self.skill_id})
        except Exception as e:
            return SkillOutput(success=False, error=str(e))
