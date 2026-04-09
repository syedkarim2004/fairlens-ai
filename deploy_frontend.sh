#!/bin/bash
# deploy_frontend.sh — Professional Cloud Deployment Script for FairLens AI

set -e # Exit on error

# ---------------------------------------------------------------------------
# 1. Build the Frontend
# ---------------------------------------------------------------------------
echo "🚀 Building FairLens Frontend (Vite)..."
cd frontend
npm install && npm install --save-dev firebase-tools
npm run build
cd ..

# ---------------------------------------------------------------------------
# 3. Deploy to Firebase Hosting (Unified Domain)
# ---------------------------------------------------------------------------
echo "☁️ Deploying to Firebase Hosting..."

# We use the Firebase CLI to deploy to the unified domain [fairlens-2026]
cd frontend
npx firebase deploy --only hosting --project fairlens-2026 --non-interactive
cd ..

echo "✅ Unified deployment complete!"
echo "🔗 App is live at: https://fairlens-2026.web.app"
