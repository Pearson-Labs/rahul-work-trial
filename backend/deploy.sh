#!/bin/bash

# 🚀 Vercel Deployment Script for Enhanced AI Contract Analysis Platform

echo "🚀 Starting Vercel deployment..."
echo "=================================="

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

echo "✅ Vercel CLI ready"

# Deploy to Vercel
echo "📡 Deploying to Vercel..."
echo "🔐 Please run 'vercel login' first if you haven't already"
echo "Then run: vercel --prod --yes"
echo ""
echo "Or simply run: vercel"
echo "And follow the interactive prompts"

echo ""
echo "🎉 Deployment complete!"
echo "=================================="
echo ""
echo "📋 Next steps:"
echo "1. Configure environment variables in Vercel dashboard"
echo "2. Update CORS origins in main.py if needed"
echo "3. Test the deployed endpoints"
echo ""
echo "📚 For detailed instructions, see DEPLOYMENT.md"