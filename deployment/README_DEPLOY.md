☁️ CoderLang Enterprise Deployment Guide

This guide details how to deploy the CoderLang Multi-Agent System to Google Cloud Platform (GCP).

Prerequisites

Google Cloud Project: A project with billing enabled.

APIs Enabled:

Cloud Run API

Artifact Registry API

Vertex AI API (for the Agent Engine track)

Tools:

Google Cloud SDK (gcloud) installed and authenticated.

Option 1: Rapid Deployment (Cloud Run)

This method deploys the application as a serverless container. This includes the Streamlit Dashboard.

1. Configure Environment

Ensure you have your API key ready.

export GOOGLE_API_KEY="AIzaSy..."
export PROJECT_ID="your-project-id"


2. Run Deployment Script

We have provided an automated script to build the container and push it to Cloud Run.

chmod +x deployment/deploy.sh
./deployment/deploy.sh


What this script does:

Builds the Docker image using Cloud Build.

Pushes the image to Google Container Registry (GCR).

Deploys a Cloud Run service named coderlang-enterprise.

Exposes port 8501 (Streamlit).

3. Access the Dashboard

Once complete, the script will output a URL:
https://coderlang-enterprise-xyz-uc.a.run.app

Option 2: Vertex AI Agent Engine (Advanced)

For enterprise integration with Google's managed Agent ecosystem.

1. Create Secret

Store your API key securely.

gcloud secrets create GEMINI_API_KEY --data-file=.env


2. Deploy Agent

Use the vertex_config.yaml configuration.

gcloud ai agent-engine deploy --config-file=deployment/vertex_config.yaml


🐳 Local Docker Testing

To test the production build locally before deploying:

# Build
docker build -t coderlang .

# Run (Port 8501 mapped for Dashboard)
docker run -p 8501:8501 --env-file .env coderlang


Visit http://localhost:8501 to verify.