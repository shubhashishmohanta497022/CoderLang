☁ Deployment Guide: Vertex AI Agent Engine / Cloud Run

This guide outlines the theoretical steps and configuration for deploying the CoderLang multi-agent system to Google Cloud.

1. Prerequisites

Google Cloud Project: A valid Google Cloud project with billing enabled.

APIs: The Vertex AI API and Cloud Run API must be enabled.

Authentication: gcloud CLI installed and authenticated (gcloud auth login).

2. Docker Image Creation

The system uses the Dockerfile in the root directory. Build and push the image to Google Container Registry (GCR) or Artifact Registry (AR).

# 1. Set variables
export PROJECT_ID="your-gcp-project-id"
export REPO_NAME="coderlang-repo"
export IMAGE_NAME="gcr.io/${PROJECT_ID}/${REPO_NAME}:latest"

# 2. Build the image
docker build -t ${IMAGE_NAME} .

# 3. Push the image (ensure Docker is configured for gcr.io or AR)
docker push ${IMAGE_NAME}


3. Vertex AI Agent Engine Deployment (Advanced)

This path uses the Agent Development Kit (ADK) integration with Vertex AI. It offers managed scaling and integrates with Vertex AI's tooling (logging, monitoring).

The configuration uses the vertex_config.yaml (placeholder below).

vertex_config.yaml (Conceptual)

# deployment/vertex_config.yaml
display_name: "CoderLang-AgentEngine"
description: "Multi-Agent Coding Assistant powered by Gemini"
agent_container:
  # Reference the image built in Step 2
  image_uri: "${IMAGE_NAME}"
  # Environment variable for the API key, configured in Vertex AI Secret Manager
  env_vars:
    - name: "GOOGLE_API_KEY_SECRET"
      value: "projects/${PROJECT_ID}/secrets/GEMINI_API_KEY/versions/latest"
  # Entrypoint must point to the main execution file
  command: ["python", "main.py"]


Deployment Command:

# Assuming you have the Vertex AI ADK SDK installed
# This command registers and deploys the container as a managed agent service.
gcloud ai agent-engine deploy --config-file=deployment/vertex_config.yaml


4. Cloud Run Deployment (Simplified HTTP Service)

If CoderLang were wrapped in a simple FastAPI or Flask web endpoint, Cloud Run provides a simpler, serverless deployment option.

cloudrun.yaml (Conceptual)

# deployment/cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: coderlang-service
  annotations:
    [run.googleapis.com/ingress](https://run.googleapis.com/ingress): "all"
spec:
  template:
    spec:
      containers:
      - image: ${IMAGE_NAME}
        resources:
          limits:
            cpu: 2000m
            memory: 4Gi # LLM agents are memory intensive
        env:
          - name: GOOGLE_API_KEY
            # Secret manager is highly recommended for production
            valueFrom:
              secretKeyRef:
                name: gemini-api-key-secret
                key: latest


Deployment Command:

gcloud run deploy coderlang-service \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-secrets=GOOGLE_API_KEY=GEMINI_API_KEY:latest
