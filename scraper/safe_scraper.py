"""Safe version of unified scraper with timeouts and error handling"""

import asyncio
import signal
import sys
from unified_scraper import UnifiedLunchScraper

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

async def safe_scrape(timeout_seconds=300):
    """Run scraper with timeout protection"""
    
    print(f"🚀 Starting safe scraper with {timeout_seconds}s timeout...")
    
    # Set up timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        scraper = UnifiedLunchScraper()
        await scraper.run_full_pipeline(force_all=True)
        signal.alarm(0)  # Cancel timeout
        print("✅ Scraping completed successfully!")
        
    except TimeoutError:
        print("⏰ Scraping timed out - saving partial results...")
        signal.alarm(0)
        
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        signal.alarm(0)
        
    finally:
        print("🔄 Combining with existing data...")
        # Always combine data at the end
        import subprocess
        subprocess.run([sys.executable, "combine_data.py"])

if __name__ == "__main__":
    import sys
    
    # Get timeout from command line or use default
    timeout = 300  # 5 minutes default
    if len(sys.argv) > 1:
        try:
            timeout = int(sys.argv[1])
        except ValueError:
            print("Usage: python safe_scraper.py [timeout_seconds]")
            exit(1)
    
    print(f"Running with {timeout} second timeout...")
    asyncio.run(safe_scrape(timeout))