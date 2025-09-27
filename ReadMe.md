#!/bin/bash
# ============================================
#  IST LUNCH - COMPLETE SETUP GUIDE
# ============================================

cat << 'SETUP'

📋 QUICK START GUIDE
====================

1. CLONE & SETUP
----------------
git clone https://github.com/yourusername/ist-lunch.git
cd ist-lunch

2. SETUP GITHUB ACTIONS SECRETS
--------------------------------
Go to GitHub Settings > Secrets > Actions and add:
- OPENAI_API_KEY: Your OpenAI API key
- SUPABASE_URL: Your Supabase project URL (optional)
- SUPABASE_KEY: Your Supabase anon key (optional)

3. SETUP FRONTEND
-----------------
cd frontend
npm install
npm run dev

4. DEPLOY TO VERCEL (FREE)
---------------------------
npm i -g vercel
vercel

5. TEST SCRAPER LOCALLY
------------------------
cd scraper
pip install -r requirements.txt
playwright install chromium
python scraper.py

SETUP


# frontend/package.json
cat > frontend/package.json << 'PACKAGE'
{
  "name": "ist-lunch",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.1.0",
    "react": "^18",
    "react-dom": "^18",
    "lucide-react": "^0.309.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "autoprefixer": "^10.0.1",
    "postcss": "^8",
    "tailwindcss": "^3.3.0",
    "typescript": "^5"
  }
}
PACKAGE

# frontend/app/layout.tsx
cat > frontend/app/layout.tsx << 'LAYOUT'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'IST Lunch - Sundbybergs bästa lunchguide',
  description: 'Hitta dagens lunch i Sundbyberg med priser, hälsopoäng och kategorier',
  keywords: 'lunch, sundbyberg, restaurang, dagens lunch, mat',
  openGraph: {
    title: 'IST Lunch',
    description: 'Sundbybergs smartaste lunchguide',
    images: ['/og-image.png'],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="sv">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
LAYOUT

# frontend/app/globals.css
cat > frontend/app/globals.css << 'STYLES'
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  @apply bg-gray-100;
}

::-webkit-scrollbar-thumb {
  @apply bg-gray-400 rounded-full;
}

::-webkit-scrollbar-thumb:hover {
  @apply bg-gray-500;
}

/* Range slider styling */
input[type="range"] {
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
  cursor: pointer;
}

input[type="range"]::-webkit-slider-track {
  @apply bg-gray-200 rounded-lg h-2;
}

input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  @apply bg-blue-600 rounded-full h-4 w-4 -mt-1 cursor-pointer hover:bg-blue-700 transition;
}

input[type="range"]::-moz-range-track {
  @apply bg-gray-200 rounded-lg h-2;
}

input[type="range"]::-moz-range-thumb {
  @apply bg-blue-600 rounded-full h-4 w-4 border-0 cursor-pointer hover:bg-blue-700 transition;
}

/* Dark mode styles */
.dark {
  @apply bg-gray-900 text-gray-100;
}

.dark .bg-white {
  @apply bg-gray-800;
}

.dark .text-gray-900 {
  @apply text-gray-100;
}

.dark .text-gray-700 {
  @apply text-gray-300;
}

.dark .text-gray-600 {
  @apply text-gray-400;
}

.dark .border-gray-200 {
  @apply border-gray-700;
}

.dark .border-gray-300 {
  @apply border-gray-600;
}

.dark .bg-gray-50 {
  @apply bg-gray-800;
}

.dark .bg-gray-100 {
  @apply bg-gray-700;
}
STYLES

# frontend/app/api/menus/route.ts
cat > frontend/app/api/menus/route.ts << 'API'
import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Option 1: Fetch from GitHub (if using GitHub as database)
    const response = await fetch(
      'https://raw.githubusercontent.com/yourusername/ist-lunch/main/data/menus.json',
      { next: { revalidate: 300 } } // Cache for 5 minutes
    );
    
    if (response.ok) {
      const data = await response.json();
      return NextResponse.json(data);
    }
    
    // Option 2: Fetch from Supabase (if configured)
    if (process.env.SUPABASE_URL) {
      const { createClient } = require('@supabase/supabase-js');
      const supabase = createClient(
        process.env.SUPABASE_URL,
        process.env.SUPABASE_ANON_KEY
      );
      
      const { data: restaurants } = await supabase
        .from('restaurants')
        .select(`
          *,
          menu_items(*)
        `)
        .eq('date', new Date().toISOString().split('T')[0]);
      
      return NextResponse.json({
        generated_at: new Date().toISOString(),
        date: new Date().toISOString().split('T')[0],
        restaurants: restaurants || []
      });
    }
    
    // Fallback: Return sample data
    return NextResponse.json(getSampleData());
    
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(getSampleData());
  }
}

function getSampleData() {
  // ... sample data from the frontend component
  return { restaurants: [] };
}
API

# frontend/tailwind.config.ts
cat > frontend/tailwind.config.ts << 'TAILWIND'
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
export default config
TAILWIND

# vercel.json
cat > vercel.json << 'VERCEL'
{
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/.next",
  "installCommand": "cd frontend && npm install",
  "framework": "nextjs"
}
VERCEL

# Admin interface (simple HTML for adding restaurants)
cat > admin.html << 'ADMIN'
<!DOCTYPE html>
<html lang="sv">
<head>
  <meta charset="UTF-8">
  <title>IST Lunch Admin</title>
  <style>
    body { font-family: -apple-system, Arial; max-width: 800px; margin: 50px auto; padding: 20px; }
    h1 { color: #2563eb; }
    .form-group { margin: 20px 0; }
    label { display: block; margin-bottom: 5px; font-weight: bold; }
    input, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
    button { background: #2563eb; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
    button:hover { background: #1d4ed8; }
    #output { background: #f5f5f5; padding: 15px; margin-top: 20px; border-radius: 4px; }
    .restaurant-item { background: white; padding: 10px; margin: 10px 0; border-radius: 4px; border: 1px solid #ddd; }
  </style>
</head>
<body>
  <h1>🍽️ IST Lunch - Admin Interface</h1>
  
  <div class="form-group">
    <label>Restaurangnamn</label>
    <input type="text" id="name" placeholder="Ex: Eatery Garden Sundbyberg">
  </div>
  
  <div class="form-group">
    <label>Webbadress (URL)</label>
    <input type="url" id="url" placeholder="https://restaurang.se">
  </div>
  
  <div class="form-group">
    <label>Adress</label>
    <input type="text" id="address" placeholder="Landsvägen 50A, Sundbyberg">
  </div>
  
  <div class="form-group">
    <label>ID (kort namn, inga mellanslag)</label>
    <input type="text" id="id" placeholder="eatery-garden">
  </div>
  
  <button onclick="addRestaurant()">Lägg till restaurang</button>
  <button onclick="exportJSON()">Exportera JSON</button>
  <button onclick="testScrape()">Testa scraping</button>
  
  <div id="output">
    <h3>Tillagda restauranger:</h3>
    <div id="restaurants"></div>
    <h3>JSON Output:</h3>
    <pre id="json-output"></pre>
  </div>
  
  <script>
    let restaurants = JSON.parse(localStorage.getItem('restaurants') || '[]');
    
    function addRestaurant() {
      const restaurant = {
        id: document.getElementById('id').value,
        name: document.getElementById('name').value,
        url: document.getElementById('url').value,
        address: document.getElementById('address').value
      };
      
      if (!restaurant.id || !restaurant.name || !restaurant.url) {
        alert('Fyll i alla obligatoriska fält!');
        return;
      }
      
      restaurants.push(restaurant);
      localStorage.setItem('restaurants', JSON.stringify(restaurants));
      updateDisplay();
      clearForm();
    }
    
    function updateDisplay() {
      const html = restaurants.map(r => 
        `<div class="restaurant-item">
          <strong>${r.name}</strong><br>
          ${r.url}<br>
          ${r.address}
        </div>`
      ).join('');
      
      document.getElementById('restaurants').innerHTML = html;
      document.getElementById('json-output').textContent = 
        JSON.stringify({ restaurants }, null, 2);
    }
    
    function clearForm() {
      ['id', 'name', 'url', 'address'].forEach(id => 
        document.getElementById(id).value = ''
      );
    }
    
    function exportJSON() {
      const blob = new Blob([JSON.stringify({ restaurants }, null, 2)], 
        { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'restaurants.json';
      a.click();
    }
    
    async function testScrape() {
      const url = document.getElementById('url').value;
      if (!url) {
        alert('Ange en URL att testa!');
        return;
      }
      
      alert('Scraping test kommer snart! För nu, kör Python scriptet lokalt.');
    }
    
    // Load on start
    updateDisplay();
  </script>
</body>
</html>
ADMIN

# README for complete setup
cat > README.md << 'README'
# 🍽️ IST Lunch - Sundbybergs Smartaste Lunchguide

Modern, automatiserad lunchguide som samlar dagens menyer från restauranger i Sundbyberg.

## ✨ Features

- 🤖 AI-driven menyanalys (GPT-4)
- 🔍 Smart kategorisering (Kött/Fisk/Vegetarisk/Vegansk)
- 💪 Hälsopoäng för varje rätt
- 🏷️ Dietmärkning (high-protein, low-carb, etc)
- 🔄 Automatisk uppdatering varje vardag kl 10:00
- 📱 Responsiv design
- 🌙 Dark mode
- 💰 Gratis hosting (Vercel + GitHub Actions)

## 🚀 Quick Start

### 1. Fork & Clone
```bash
git clone https://github.com/yourusername/ist-lunch.git
cd ist-lunch
```

### 2. Setup Secrets
Gå till GitHub Settings > Secrets > Actions och lägg till:
- `OPENAI_API_KEY`: Din OpenAI API nyckel

### 3. Starta lokalt
```bash
# Frontend
cd frontend
npm install
npm run dev

# Scraper (test)
cd scraper
pip install -r requirements.txt
python scraper.py
```

### 4. Deploy till Vercel (gratis)
```bash
npm i -g vercel
vercel
```

## 📊 Kostnad

| Tjänst | Kostnad/månad |
|--------|---------------|
| Vercel hosting | 0 kr |
| GitHub Actions | 0 kr |
| GPT-4o-mini | ~20 kr |
| **TOTALT** | **~20 kr** |

## 🏗️ Arkitektur

```
GitHub Actions (10:00) → Python Scraper → GPT-4 → JSON → Vercel
```

## 📝 Lägg till restauranger

Öppna `admin.html` i webbläsaren och lägg till restauranger.
Exportera JSON och uppdatera `scraper/restaurants.json`.

## 🔧 Konfiguration

### Ändra scrapningstider
Redigera `.github/workflows/scrape-menus.yml`:
```yaml
schedule:
  - cron: '0 8 * * 1-5'  # 10:00 svensk tid
```

### Anpassa hälsopoäng
Redigera `scraper/scraper.py` för att justera algoritmen.

## 📈 Framtida förbättringar

- [ ] Användarrecensioner
- [ ] Favoritmarkering
- [ ] Push-notifikationer
- [ ] Betalda premium-features

## 📄 Licens

MIT

## 🤝 Bidra

Pull requests välkomna! 

---
Byggd med ❤️ för hungriga Sundbybergare
README