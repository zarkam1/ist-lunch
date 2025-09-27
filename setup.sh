#!/bin/bash

# =====================================================
#  IST LUNCH - QUICK SETUP SCRIPT
#  Run this to set up the entire project
# =====================================================

echo "🍽️  IST LUNCH - Quick Setup"
echo "=========================="
echo ""

# Check if we're in the right directory
if [ ! -f "scraper/scraper.py" ]; then
    echo "❌ Error: Please run this script from the ist-lunch root directory"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Check prerequisites
echo "📋 Checking prerequisites..."

if ! command_exists node; then
    echo "❌ Node.js not found. Please install from: https://nodejs.org/"
    exit 1
fi
echo "✅ Node.js found: $(node --version)"

if ! command_exists python3; then
    if ! command_exists python; then
        echo "❌ Python not found. Please install Python 3.11+"
        exit 1
    fi
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi
echo "✅ Python found: $($PYTHON_CMD --version)"

if ! command_exists npm; then
    echo "❌ npm not found. Please install npm"
    exit 1
fi
echo "✅ npm found: $(npm --version)"

echo ""

# 2. Install Frontend Dependencies
echo "📦 Installing Frontend Dependencies..."
cd frontend

# Create package.json if it doesn't exist
if [ ! -f "package.json" ]; then
    echo "Creating package.json..."
    npm init -y
    npm pkg set name="ist-lunch-frontend"
    npm pkg set version="1.0.0"
    npm pkg set scripts.dev="next dev"
    npm pkg set scripts.build="next build"
    npm pkg set scripts.start="next start"
fi

# Install dependencies
npm install next@latest react@latest react-dom@latest
npm install -D typescript @types/react @types/node
npm install lucide-react clsx tailwind-merge
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

echo "✅ Frontend dependencies installed"
cd ..
echo ""

# 3. Install Python Dependencies
echo "🐍 Installing Python Dependencies..."
cd scraper

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
if [ -f "venv/Scripts/activate" ]; then
    # Windows Git Bash
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    # Mac/Linux
    source venv/bin/activate
else
    echo "⚠️  Could not activate virtual environment"
fi

# Install Python packages
pip install --upgrade pip
pip install playwright beautifulsoup4 aiohttp openai lxml python-dotenv

# Install Playwright browsers
echo "Installing Playwright browser (this may take a minute)..."
playwright install chromium

echo "✅ Python dependencies installed"
cd ..
echo ""

# 4. Create necessary directories
echo "📁 Creating project directories..."
mkdir -p frontend/app/api/menus
mkdir -p frontend/components
mkdir -p frontend/public
mkdir -p data
mkdir -p .github/workflows

echo "✅ Directories created"
echo ""

# 5. Create environment files
echo "🔐 Creating environment files..."

# Create .env.local for frontend
if [ ! -f "frontend/.env.local" ]; then
    cat > frontend/.env.local << EOF
# OpenAI API Key (required)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: Supabase (if you want to use it instead of GitHub storage)
# NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
# NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Site URL (update when deployed)
NEXT_PUBLIC_SITE_URL=http://localhost:3000
EOF
    echo "✅ Created frontend/.env.local"
else
    echo "⚠️  frontend/.env.local already exists, skipping"
fi

# Create .env for scraper
if [ ! -f "scraper/.env" ]; then
    cat > scraper/.env << EOF
# OpenAI API Key (required)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional: Supabase
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_KEY=your-service-role-key
EOF
    echo "✅ Created scraper/.env"
else
    echo "⚠️  scraper/.env already exists, skipping"
fi

# Create .gitignore
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << EOF
# Dependencies
node_modules/
venv/
__pycache__/
*.pyc

# Environment files
.env
.env.local
.env.production

# Production
.next/
out/
build/
dist/

# Debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Data (if you want to keep it local)
# data/menus.json

# Playwright
playwright-report/
test-results/
EOF
    echo "✅ Created .gitignore"
fi

echo ""

# 6. Create sample restaurants.json if it doesn't exist
if [ ! -f "scraper/restaurants.json" ]; then
    echo "📝 Creating sample restaurants.json..."
    cat > scraper/restaurants.json << 'EOF'
{
  "restaurants": [
    {
      "id": "eatery-garden",
      "name": "Eatery Garden Sundbyberg",
      "url": "https://eatery.se/garden-sundbyberg",
      "address": "Landsvägen 50A, 172 63 Sundbyberg",
      "lat": 59.3608,
      "lon": 17.9689
    },
    {
      "id": "ristorante-parma",
      "name": "Ristorante Parma",
      "url": "https://ristoranteparma.se",
      "address": "Sturegatan 32, 172 31 Sundbyberg",
      "lat": 59.3612,
      "lon": 17.9658
    },
    {
      "id": "kitchin-sundbyberg",
      "name": "Kitchin by Kasai",
      "url": "https://kitchin.se/signalfabriken-sundbyberg",
      "address": "Ursviksvägen 6, 172 66 Sundbyberg",
      "lat": 59.3627,
      "lon": 17.9742
    }
  ]
}
EOF
    echo "✅ Created scraper/restaurants.json"
fi

echo ""

# 7. Test installation
echo "🧪 Testing installation..."

# Test Node/npm
cd frontend
if npm list next &>/dev/null; then
    echo "✅ Next.js installed correctly"
else
    echo "⚠️  Next.js installation may have issues"
fi
cd ..

# Test Python
cd scraper
if $PYTHON_CMD -c "import playwright, bs4, aiohttp, openai" 2>/dev/null; then
    echo "✅ Python packages installed correctly"
else
    echo "⚠️  Some Python packages may be missing"
fi
cd ..

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Add your OpenAI API key:"
echo "   Edit frontend/.env.local and scraper/.env"
echo "   Get key from: https://platform.openai.com/api-keys"
echo ""
echo "2. Start the frontend:"
echo "   cd frontend"
echo "   npm run dev"
echo "   Open http://localhost:3000"
echo ""
echo "3. Test the scraper:"
echo "   cd scraper"
echo "   python scraper.py"
echo ""
echo "4. Deploy to Vercel:"
echo "   npm i -g vercel"
echo "   vercel"
echo ""
echo "5. Setup GitHub Actions:"
echo "   git init"
echo "   git add ."
echo "   git commit -m 'Initial commit'"
echo "   git remote add origin YOUR_GITHUB_URL"
echo "   git push -u origin main"
echo ""
echo "Need help? Check claude.md for detailed instructions!"
echo "🍽️  Happy lunching!"

# Create a simple test script
cat > test-setup.sh << 'EOF'
#!/bin/bash
echo "Testing IST Lunch Setup..."
echo "1. Checking frontend..."
cd frontend && npm run build && echo "✅ Frontend OK" || echo "❌ Frontend failed"
echo "2. Checking scraper..."
cd ../scraper && python -c "import scraper; print('✅ Scraper OK')" || echo "❌ Scraper failed"
EOF
chmod +x test-setup.sh

echo ""
echo "💡 Tip: Run ./test-setup.sh to verify everything works!"