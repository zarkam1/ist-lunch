#!/bin/bash
echo "Testing IST Lunch Setup..."
echo "1. Checking frontend..."
cd frontend && npm run build && echo "✅ Frontend OK" || echo "❌ Frontend failed"
echo "2. Checking scraper..."
cd ../scraper && python -c "import scraper; print('✅ Scraper OK')" || echo "❌ Scraper failed"
