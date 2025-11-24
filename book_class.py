#!/usr/bin/env python3
"""
MindBody Auto Booking Script
Automates booking of fitness classes at Studio Locomotion via MindBody Online
"""

import os
import json
import sys
import random
import time
import math
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from twocaptcha import TwoCaptcha
import traceback


# ============================================================
# ANTI-BOT DETECTION UTILITIES
# ============================================================

def get_random_user_agent():
    """Return a random realistic user agent"""
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    ]
    return random.choice(user_agents)


def get_stealth_scripts():
    """Return JavaScript to hide automation indicators"""
    return """
    // Override the navigator.webdriver property
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    
    // Override the navigator.plugins to appear more realistic
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5]
    });
    
    // Override chrome runtime
    window.chrome = {
        runtime: {}
    };
    
    // Add realistic permissions
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
    
    // Randomize canvas fingerprint
    const getImageData = CanvasRenderingContext2D.prototype.getImageData;
    CanvasRenderingContext2D.prototype.getImageData = function(...args) {
        const imageData = getImageData.apply(this, args);
        for (let i = 0; i < imageData.data.length; i += 4) {
            imageData.data[i] += Math.floor(Math.random() * 3) - 1;
            imageData.data[i + 1] += Math.floor(Math.random() * 3) - 1;
            imageData.data[i + 2] += Math.floor(Math.random() * 3) - 1;
        }
        return imageData;
    };
    
    // Randomize WebGL fingerprint
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) {
            return 'Intel Inc.';
        }
        if (parameter === 37446) {
            return 'Intel Iris OpenGL Engine';
        }
        return getParameter.apply(this, [parameter]);
    };
    """


def human_mouse_move(page, x, y):
    """Move mouse in a human-like curved path"""
    try:
        # Get current mouse position (start from a random position if unknown)
        current_x = random.randint(100, 500)
        current_y = random.randint(100, 500)
        
        # Calculate control points for Bezier curve
        ctrl_x1 = current_x + (x - current_x) * 0.3 + random.randint(-50, 50)
        ctrl_y1 = current_y + (y - current_y) * 0.3 + random.randint(-50, 50)
        ctrl_x2 = current_x + (x - current_x) * 0.7 + random.randint(-50, 50)
        ctrl_y2 = current_y + (y - current_y) * 0.7 + random.randint(-50, 50)
        
        # Move along the curve
        steps = random.randint(10, 20)
        for i in range(steps + 1):
            t = i / steps
            # Cubic Bezier curve formula
            pos_x = (1-t)**3 * current_x + 3*(1-t)**2*t * ctrl_x1 + 3*(1-t)*t**2 * ctrl_x2 + t**3 * x
            pos_y = (1-t)**3 * current_y + 3*(1-t)**2*t * ctrl_y1 + 3*(1-t)*t**2 * ctrl_y2 + t**3 * y
            
            page.mouse.move(pos_x, pos_y)
            time.sleep(random.uniform(0.001, 0.005))
        
        # Add small jitter at the end
        for _ in range(random.randint(1, 3)):
            jitter_x = x + random.randint(-2, 2)
            jitter_y = y + random.randint(-2, 2)
            page.mouse.move(jitter_x, jitter_y)
            time.sleep(random.uniform(0.01, 0.03))
            
    except Exception as e:
        print(f"  Mouse movement error (non-critical): {str(e)}")


def human_type(element, text, page=None):
    """Type text in a human-like way with variable speed and occasional pauses"""
    try:
        # Sometimes make a typo and correct it
        if random.random() < 0.05:  # 5% chance of typo
            typo_pos = random.randint(0, len(text) - 1)
            wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
            
            # Type up to the typo
            for char in text[:typo_pos]:
                element.type(char, delay=random.uniform(50, 150))
            
            # Type wrong character
            element.type(wrong_char, delay=random.uniform(50, 150))
            time.sleep(random.uniform(0.1, 0.3))
            
            # Delete it (backspace)
            element.press('Backspace')
            time.sleep(random.uniform(0.05, 0.15))
            
            # Continue with correct text
            for char in text[typo_pos:]:
                element.type(char, delay=random.uniform(50, 150))
        else:
            # Normal typing with variable speed
            for i, char in enumerate(text):
                element.type(char, delay=random.uniform(50, 200))
                
                # Occasional longer pause (thinking)
                if random.random() < 0.1:  # 10% chance
                    time.sleep(random.uniform(0.2, 0.5))
                    
    except Exception as e:
        # Fallback to regular fill
        print(f"  Human typing failed, using regular fill: {str(e)}")
        element.fill(text)


def random_scroll(page, direction='down', amount=None):
    """Scroll page in a human-like manner"""
    try:
        if amount is None:
            amount = random.randint(300, 800)
        
        # Scroll in chunks with pauses
        chunks = random.randint(3, 6)
        chunk_size = amount // chunks
        
        for i in range(chunks):
            if direction == 'down':
                page.evaluate(f'window.scrollBy(0, {chunk_size})')
            else:
                page.evaluate(f'window.scrollBy(0, -{chunk_size})')
            
            time.sleep(random.uniform(0.05, 0.15))
        
        # Small back-scroll (humans often do this)
        if random.random() < 0.3:
            back_amount = random.randint(20, 100)
            if direction == 'down':
                page.evaluate(f'window.scrollBy(0, -{back_amount})')
            else:
                page.evaluate(f'window.scrollBy(0, {back_amount})')
            time.sleep(random.uniform(0.1, 0.2))
            
    except Exception as e:
        print(f"  Scroll error (non-critical): {str(e)}")


def random_mouse_movement(page):
    """Move mouse randomly across the page (like a human browsing)"""
    try:
        viewport = page.viewport_size
        if viewport:
            # Move to a few random positions
            for _ in range(random.randint(1, 3)):
                x = random.randint(100, viewport['width'] - 100)
                y = random.randint(100, viewport['height'] - 100)
                human_mouse_move(page, x, y)
                time.sleep(random.uniform(0.1, 0.3))
    except Exception as e:
        print(f"  Random mouse movement error (non-critical): {str(e)}")


def human_click(element, page=None):
    """Click element with human-like behavior"""
    try:
        # Move mouse to element first
        if page:
            box = element.bounding_box()
            if box:
                # Click slightly off-center (humans don't click exact center)
                target_x = box['x'] + box['width'] / 2 + random.randint(-5, 5)
                target_y = box['y'] + box['height'] / 2 + random.randint(-5, 5)
                human_mouse_move(page, target_x, target_y)
                time.sleep(random.uniform(0.1, 0.3))
        
        # Slight delay before click
        time.sleep(random.uniform(0.05, 0.15))
        element.click()
        
        # Slight delay after click
        time.sleep(random.uniform(0.1, 0.25))
        
    except Exception as e:
        # Fallback to regular click
        print(f"  Human click failed, using regular click: {str(e)}")
        element.click()


def random_idle_behavior(page):
    """Perform random idle behaviors like a human reading the page"""
    try:
        behavior = random.choice(['scroll_tiny', 'mouse_wiggle', 'pause', 'scroll_up_down'])
        
        if behavior == 'scroll_tiny':
            # Small scroll (like reading)
            page.evaluate(f'window.scrollBy(0, {random.randint(-30, 50)})')
            time.sleep(random.uniform(0.1, 0.3))
            
        elif behavior == 'mouse_wiggle':
            # Small mouse movements
            viewport = page.viewport_size
            if viewport:
                current_x = random.randint(200, viewport['width'] - 200)
                current_y = random.randint(200, viewport['height'] - 200)
                for _ in range(random.randint(2, 4)):
                    page.mouse.move(
                        current_x + random.randint(-30, 30),
                        current_y + random.randint(-30, 30)
                    )
                    time.sleep(random.uniform(0.05, 0.15))
                    
        elif behavior == 'pause':
            # Just pause (reading)
            time.sleep(random.uniform(0.5, 1.5))
            
        elif behavior == 'scroll_up_down':
            # Scroll down then back up (checking something)
            page.evaluate(f'window.scrollBy(0, {random.randint(100, 200)})')
            time.sleep(random.uniform(0.2, 0.5))
            page.evaluate(f'window.scrollBy(0, -{random.randint(50, 100)})')
            time.sleep(random.uniform(0.1, 0.3))
            
    except Exception as e:
        print(f"  Idle behavior error (non-critical): {str(e)}")


def load_config():
    """Load configuration from config.json"""
    with open('config.json', 'r') as f:
        return json.load(f)


def get_password():
    """Get password from environment variable"""
    password = os.environ.get('MINDBODY_PASSWORD')
    if not password:
        raise ValueError("MINDBODY_PASSWORD environment variable not set")
    return password


def get_captcha_api_key(config):
    """Get 2captcha API key from config"""
    api_key = config.get('captcha_api_key')
    if not api_key:
        raise ValueError("captcha_api_key not found in config.json")
    return api_key


def human_delay(min_ms=1000, max_ms=3000):
    """Add random human-like delay"""
    delay = random.randint(min_ms, max_ms)
    time.sleep(delay / 1000.0)


def extract_recaptcha_sitekey(page):
    """Extract the reCAPTCHA sitekey from the page"""
    try:
        print("  Extracting reCAPTCHA sitekey...")
        
        # Method 1: Look for data-sitekey attribute in divs
        sitekey_elem = page.query_selector('[data-sitekey]')
        if sitekey_elem:
            sitekey = sitekey_elem.get_attribute('data-sitekey')
            if sitekey:
                print(f"  ✓ Found sitekey via data-sitekey attribute: {sitekey}")
                return sitekey
        
        # Method 2: Extract from reCAPTCHA iframe src
        recaptcha_frames = page.query_selector_all('iframe[src*="recaptcha"]')
        for frame in recaptcha_frames:
            src = frame.get_attribute('src')
            if src and 'k=' in src:
                # Extract sitekey from URL parameter k=SITEKEY
                import re
                match = re.search(r'[?&]k=([^&]+)', src)
                if match:
                    sitekey = match.group(1)
                    print(f"  ✓ Found sitekey from iframe URL: {sitekey}")
                    return sitekey
        
        # Method 3: Search in page source for grecaptcha.render or grecaptcha.execute calls
        page_content = page.content()
        import re
        patterns = [
            r'grecaptcha\.render\([^,]+,\s*{\s*["\']?sitekey["\']?\s*:\s*["\']([^"\']+)["\']',
            r'grecaptcha\.execute\(["\']([^"\']+)["\']',
            r'data-sitekey=["\']([^"\']+)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_content)
            if match:
                sitekey = match.group(1)
                print(f"  ✓ Found sitekey in page source: {sitekey}")
                return sitekey
        
        print("  ✗ Could not find reCAPTCHA sitekey")
        return None
        
    except Exception as e:
        print(f"  Error extracting sitekey: {str(e)}")
        return None


def inject_recaptcha_solution(page, solution_token):
    """Inject the reCAPTCHA solution token into the page"""
    try:
        print("  Injecting reCAPTCHA solution...")
        
        # Method 1: Set g-recaptcha-response textarea value
        inject_script = f"""
        (function() {{
            // Find all g-recaptcha-response textareas
            var elements = document.getElementsByName('g-recaptcha-response');
            for (var i = 0; i < elements.length; i++) {{
                elements[i].innerHTML = '{solution_token}';
                elements[i].value = '{solution_token}';
            }}
            
            // Also set by ID if exists
            var byId = document.getElementById('g-recaptcha-response');
            if (byId) {{
                byId.innerHTML = '{solution_token}';
                byId.value = '{solution_token}';
            }}
            
            // Try to trigger callback
            if (typeof window.___grecaptcha_cfg !== 'undefined') {{
                var clients = window.___grecaptcha_cfg.clients;
                for (var id in clients) {{
                    var client = clients[id];
                    if (client && client.callback) {{
                        try {{
                            client.callback('{solution_token}');
                        }} catch(e) {{
                            console.log('Callback error:', e);
                        }}
                    }}
                }}
            }}
            
            // Alternative callback trigger
            if (typeof window.recaptchaCallback !== 'undefined') {{
                try {{
                    window.recaptchaCallback('{solution_token}');
                }} catch(e) {{}}
            }}
            
            return true;
        }})();
        """
        
        page.evaluate(inject_script)
        print("  ✓ Solution token injected successfully")
        
        # Give the page a moment to process the solution
        time.sleep(1)
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error injecting solution: {str(e)}")
        return False


def solve_recaptcha_v2(page, config, max_retries=None):
    """Solve reCAPTCHA v2 using 2captcha service"""
    if max_retries is None:
        max_retries = config.get('captcha_max_retries', 5)
    
    print(f"\n{'='*60}")
    print("🤖 ATTEMPTING AUTOMATIC CAPTCHA SOLVING WITH 2CAPTCHA")
    print(f"{'='*60}")
    
    for attempt in range(1, max_retries + 1):
        print(f"\n--- Attempt {attempt}/{max_retries} ---")
        
        try:
            # Extract sitekey
            sitekey = extract_recaptcha_sitekey(page)
            if not sitekey:
                print(f"  ✗ Could not extract sitekey (attempt {attempt}/{max_retries})")
                if attempt < max_retries:
                    print(f"  Waiting 3 seconds before retry...")
                    time.sleep(3)
                    continue
                else:
                    return False
            
            # Get page URL
            page_url = page.url
            print(f"  Page URL: {page_url}")
            print(f"  Sitekey: {sitekey}")
            
            # Initialize 2captcha solver
            api_key = get_captcha_api_key(config)
            solver = TwoCaptcha(api_key)
            
            print(f"  📤 Sending CAPTCHA to 2captcha service...")
            print(f"  ⏳ This may take 30-60 seconds...")
            
            # Send CAPTCHA to 2captcha and wait for solution
            try:
                result = solver.recaptcha(
                    sitekey=sitekey,
                    url=page_url
                )
                
                solution_token = result['code']
                print(f"  ✓ Received solution from 2captcha!")
                print(f"  Solution token: {solution_token[:50]}...")
                
                # Check account balance
                try:
                    balance = solver.balance()
                    print(f"  💰 2captcha balance: ${balance}")
                    if float(balance) < 1.0:
                        print(f"  ⚠️ WARNING: Low balance! Consider adding funds.")
                except:
                    pass
                
            except Exception as e:
                error_msg = str(e).lower()
                print(f"  ✗ 2captcha error: {str(e)}")
                
                # Handle specific errors
                if 'insufficient' in error_msg or 'balance' in error_msg:
                    print(f"  ❌ INSUFFICIENT BALANCE - Cannot continue")
                    return False
                elif 'key' in error_msg or 'api' in error_msg:
                    print(f"  ❌ API KEY ERROR - Check your configuration")
                    return False
                elif 'timeout' in error_msg:
                    print(f"  ⏱️ Timeout waiting for solution")
                    if attempt < max_retries:
                        print(f"  Retrying...")
                        time.sleep(2)
                        continue
                    else:
                        return False
                else:
                    # Generic error - retry
                    if attempt < max_retries:
                        print(f"  Retrying in 5 seconds...")
                        time.sleep(5)
                        continue
                    else:
                        return False
            
            # Inject solution into page
            if inject_recaptcha_solution(page, solution_token):
                print(f"  ✓ CAPTCHA solution applied successfully!")
                
                # Wait for page to process the solution
                time.sleep(2)
                
                # Verify CAPTCHA is gone
                if not detect_captcha(page):
                    print(f"  ✓✓ CAPTCHA SOLVED AND VERIFIED!")
                    print(f"{'='*60}\n")
                    return True
                else:
                    print(f"  ⚠️ Solution applied but CAPTCHA still visible")
                    if attempt < max_retries:
                        print(f"  Retrying...")
                        time.sleep(2)
                        continue
                    else:
                        return False
            else:
                print(f"  ✗ Failed to inject solution")
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                else:
                    return False
                    
        except Exception as e:
            print(f"  ✗ Unexpected error in attempt {attempt}: {str(e)}")
            print(f"  {traceback.format_exc()}")
            if attempt < max_retries:
                print(f"  Retrying in 3 seconds...")
                time.sleep(3)
                continue
            else:
                return False
    
    print(f"\n❌ Failed to solve CAPTCHA after {max_retries} attempts")
    print(f"{'='*60}\n")
    return False


def detect_captcha(page):
    """Detect if we're on a CAPTCHA or verification page"""
    try:
        # Check for common CAPTCHA indicators in URL first (most reliable)
        page_url = page.url.lower()
        url_indicators = ['recaptcha', 'captcha', 'challenge', 'verify']
        
        for indicator in url_indicators:
            if indicator in page_url:
                print(f"  CAPTCHA detected in URL: {indicator}")
                return True
        
        # Check for visible CAPTCHA elements (iframes)
        captcha_selectors = [
            'iframe[src*="recaptcha"]',
            'iframe[src*="captcha"]',
            'iframe[title*="reCAPTCHA"]',
            '[class*="recaptcha"]',
            '[id*="recaptcha"]'
        ]
        
        for selector in captcha_selectors:
            elem = page.query_selector(selector)
            if elem:
                try:
                    if elem.is_visible():
                        print(f"  CAPTCHA detected: visible element with selector {selector}")
                        return True
                except:
                    pass
        
        # Check page content for CAPTCHA indicators
        page_content = page.content().lower()
        content_indicators = [
            'verify you are human',
            'verify you\'re human',
            'security check',
            'please verify',
            'select all images',
            'image verification',
            'i\'m not a robot',
            'prove you are human'
        ]
        
        for indicator in content_indicators:
            if indicator in page_content:
                print(f"  CAPTCHA detected in content: '{indicator}'")
                return True
        
        # Check page title
        try:
            page_title = page.title().lower()
            if 'captcha' in page_title or 'verify' in page_title:
                print(f"  CAPTCHA detected in page title: {page_title}")
                return True
        except:
            pass
                
        return False
    except Exception as e:
        print(f"  Error in CAPTCHA detection: {str(e)}")
        return False


def get_target_classes(config):
    """Determine which classes to book based on current day"""
    today = datetime.now()
    day_name = today.strftime('%A').lower()
    
    if day_name == 'friday':
        return config['booking_schedule']['friday']
    elif day_name == 'saturday':
        return config['booking_schedule']['saturday']
    elif day_name == 'sunday':
        # TEST MODE: Allow Sunday for testing Monday bookings
        return config['booking_schedule'].get('sunday')
    elif day_name == 'monday':
        # TEMPORARY: Allow Monday for testing 2captcha integration
        print("⚠️ RUNNING IN TEST MODE (Monday) - Using Sunday config for Tuesday booking")
        return config['booking_schedule'].get('sunday')
    else:
        print(f"Not a booking day (today is {day_name}). Script should run on Friday, Saturday, or Sunday (test mode).")
        return None


def calculate_target_date(target_day):
    """Calculate the target date for booking"""
    today = datetime.now()
    target_day_lower = target_day.lower()
    current_weekday = today.weekday()  # Monday is 0, Sunday is 6
    
    # Map day names to weekday numbers
    day_mapping = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }
    
    target_weekday = day_mapping.get(target_day_lower)
    
    if target_weekday is None:
        # Default to tomorrow
        days_to_add = 1
    else:
        # Calculate days until target day
        days_to_add = (target_weekday - current_weekday) % 7
        
        # If it's 0, we want next week (not today)
        if days_to_add == 0:
            days_to_add = 7
    
    target_date = today + timedelta(days=days_to_add)
    return target_date


def login(page, config, password):
    """Handle login flow"""
    print("Navigating to MindBody homepage...")
    page.goto(config['homepage'], wait_until='load', timeout=60000)
    human_delay(2000, 4000)
    
    # Random browsing behavior
    random_mouse_movement(page)
    if random.random() < 0.5:
        random_idle_behavior(page)
    
    # Handle cookie consent popup - remove ALL overlays
    print("Removing any cookie consent overlays...")
    try:
        page.evaluate('''() => {
            // Remove all trust-e / cookie consent overlays
            const overlays = document.querySelectorAll('.truste_overlay, .truste_cm_outerdiv, [id*="pop-"], [class*="truste"]');
            overlays.forEach(el => el.remove());
            console.log('Removed', overlays.length, 'overlay elements');
        }''')
        human_delay(800, 1500)
        print("Removed cookie consent overlays")
    except Exception as e:
        print(f"Cookie popup handling: {str(e)}")
    
    print("Looking for Sign In button...")
    # Try to find and click the Sign In button
    sign_in_selectors = [
        'button:has-text("Sign in")',
        'a:has-text("Sign in")',
        'button:has-text("Log in")',
        'a:has-text("Log in")',
        '[data-testid*="sign-in"]',
        '[data-testid*="login"]'
    ]
    
    sign_in_button = None
    for selector in sign_in_selectors:
        try:
            sign_in_button = page.wait_for_selector(selector, timeout=5000)
            if sign_in_button:
                print(f"Found Sign In button: {selector}")
                break
        except:
            continue
    
    if sign_in_button:
        print("Clicking Sign In button...")
        random_mouse_movement(page)  # Move mouse naturally first
        human_click(sign_in_button, page)
        print("Waiting for login page to load...")
        page.wait_for_load_state('load', timeout=30000)
        human_delay(2000, 3000)
    else:
        print("Sign In button not found, may already be logged in or on login page")
    
    # Check if we need to login
    print(f"Current URL: {page.url}")
    
    # If we're already on the signin page, skip the button clicking
    if 'signin.mindbodyonline.com' in page.url or 'login' in page.url.lower():
        print("Already on login page, proceeding with login...")
    else:
        print("Not on login page yet, need to navigate there...")
    
    print(f"Entering email: {config['email']}")
    
    # Random mouse movement (like browsing)
    random_mouse_movement(page)
    human_delay(500, 1000)
    
    # Take screenshot for debugging
    page.screenshot(path='debug_login_page.png')
    print("Screenshot saved as debug_login_page.png")
    
    # Try to find email input
    try:
        email_input = page.wait_for_selector('input[type="email"], input[name="email"], input#email, input[id="EmailAddress"], input[placeholder*="email"]', timeout=5000)
    except:
        print("Standard email input not found. Trying alternative selectors...")
        # Try finding any input field
        all_inputs = page.query_selector_all('input')
        print(f"Found {len(all_inputs)} input fields")
        email_input = page.wait_for_selector('input', timeout=10000)
    
    # Click on email input first
    human_click(email_input, page)
    human_delay(200, 500)
    
    # Type email in human-like way
    human_type(email_input, config['email'], page)
    human_delay(300, 700)
    
    print("Clicking continue button...")
    continue_button = page.wait_for_selector('button:has-text("Continue"), button[type="submit"], input[type="submit"]', timeout=10000)
    human_click(continue_button, page)
    human_delay(1500, 2500)
    
    print("Entering password...")
    password_input = page.wait_for_selector('input[type="password"], input[name="password"], input[id="Password"]', timeout=10000)
    
    # Click on password input first
    human_click(password_input, page)
    human_delay(200, 500)
    
    # Type password in human-like way
    human_type(password_input, password, page)
    human_delay(300, 700)
    
    print("Submitting login form...")
    submit_button = page.wait_for_selector('button[type="submit"], button:has-text("Sign in"), button:has-text("Log in"), input[type="submit"]', timeout=10000)
    human_click(submit_button, page)
    
    print("Waiting for authentication to complete...")
    page.wait_for_load_state('load', timeout=30000)
    human_delay(2000, 4000)
    print("Login successful!")


def book_class(page, config, class_info, target_date, password, max_retries=5):
    """Book a specific class with retry logic"""
    print(f"\n{'='*60}")
    print(f"Attempting to book: {class_info['name']} at {class_info['time']}")
    print(f"Target date: {target_date.strftime('%A, %B %d, %Y')}")
    print(f"{'='*60}\n")
    
    for attempt in range(1, max_retries + 1):
        print(f"Booking attempt {attempt}/{max_retries}...")
        try:
            success = _attempt_booking(page, config, class_info, target_date, password, attempt)
            if success:
                return True
            else:
                if attempt < max_retries:
                    print(f"Attempt {attempt} failed, retrying...")
                    human_delay(2000, 4000)
        except Exception as e:
            print(f"Attempt {attempt} error: {str(e)}")
            if attempt < max_retries:
                print(f"Retrying after error...")
                human_delay(2000, 4000)
    
    print(f"Failed to book after {max_retries} attempts")
    return False


def _attempt_booking(page, config, class_info, target_date, password, attempt_num):
    """Single attempt to book a class"""
    # Navigate to studio page
    print("Navigating to Studio Locomotion page...")
    page.goto(config['studio_url'], wait_until='load', timeout=60000)
    human_delay(2000, 4000)  # Human-like delay
    
    # Random mouse movement (simulate browsing)
    random_mouse_movement(page)
    
    # Handle cookie consent popup on studio page  
    print("Checking for cookie consent on studio page...")
    try:
        # Wait for popup to appear
        human_delay(2000, 3000)
        
        # Try Playwright frames approach
        print("Looking for consent button in frames...")
        frames = page.frames
        print(f"Found {len(frames)} frames")
        
        button_clicked = False
        for frame in frames:
            try:
                # Try to find the button in this frame
                button = frame.locator('button:has-text("AGREE AND PROCEED"), button:has-text("PROCEED")').first
                if button.is_visible(timeout=1000):
                    print(f"Found button in frame: {frame.url}")
                    button.click(timeout=5000)
                    button_clicked = True
                    print("Clicked AGREE AND PROCEED button")
                    human_delay(1500, 2500)
                    break
            except:
                continue
        
        if not button_clicked:
            print("Button not found in frames, trying main page...")
            try:
                button = page.locator('button:has-text("AGREE AND PROCEED")').first
                button.click(force=True, timeout=5000)
                print("Clicked button on main page")
                human_delay(1500, 2500)
            except:
                print("Could not find/click consent button, continuing anyway...")
        
    except Exception as e:
        print(f"Cookie popup handling: {str(e)}")
    
    # Simulate reading the page
    if random.random() < 0.4:
        random_idle_behavior(page)
    human_delay(500, 1000)
    
    # Format date for searching
    target_day = target_date.strftime('%d').lstrip('0')  # Day without leading zero
    target_day_padded = target_date.strftime('%d')  # Day with leading zero
    target_month = target_date.strftime('%B')  # Full month name
    target_weekday = target_date.strftime('%a').upper()  # MON, TUE, etc.
    
    print(f"Looking for date: {target_weekday} {target_day} ({target_month})")
    
    # Find and click the target date
    # The calendar shows dates like "MON\n24" in the UI
    print("Searching for date button in calendar...")
    try:
        # Try to find the date - look for the day number in the calendar area
        # The structure is typically: day name (MON, TUE) and number (24) in separate elements
        date_found = False
        
        # Try clicking on text containing just the day number
        all_elements = page.locator(f'text={target_day}').all()
        print(f"Found {len(all_elements)} elements with text '{target_day}'")
        
        for elem in all_elements:
            try:
                # Check if this is in the calendar area (not somewhere else on the page)
                elem_text = elem.inner_text()
                if elem_text.strip() == target_day or elem_text.strip() == target_day_padded:
                    print(f"Trying to click date element with text: '{elem_text}'")
                    # Move mouse to date naturally
                    human_click(elem, page)
                    date_found = True
                    print(f"Successfully clicked on date {target_day}")
                    human_delay(3000, 4000)
                    break
            except:
                continue
        
        if not date_found:
            print(f"Could not find clickable date for {target_day}")
            print("Taking screenshot for debugging...")
            page.screenshot(path=f'error_date_not_found_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            return False
            
    except Exception as e:
        print(f"Error finding date: {str(e)}")
        page.screenshot(path=f'error_date_search_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        return False
    
    # Find the specific class
    print(f"Searching for class: {class_info['name']} at {class_info['time']}")
    
    # Look for class card containing the time and name
    time_str = class_info['time'].lower().replace('am', '').replace('pm', '').strip()
    
    # Try to find class elements
    try:
        # Wait for classes to load
        page.wait_for_selector('[class*="class"], [data-testid*="class"], .schedule-item', timeout=10000)
        human_delay(2000, 3000)
        
        # Simulate reading the page
        random_idle_behavior(page)
        human_delay(500, 1000)
        
        # Scroll down slowly to load all classes (more human-like)
        print("Scrolling to load all classes...")
        for i in range(5):
            random_scroll(page, direction='down', amount=random.randint(600, 900))
            human_delay(400, 800)
            # Occasional mouse movement while scrolling (very human)
            if random.random() < 0.3:
                random_mouse_movement(page)
        
        human_delay(1000, 2000)
        
        # BUTTON-FIRST APPROACH: Find all "Book" buttons, then verify which class they belong to
        print("Searching for class by examining all booking buttons...")
        
        target_class = None
        class_name_lower = class_info['name'].lower()
        class_type_lower = class_info['type'].lower()
        
        # Time variants for matching
        time_variants = [
            class_info['time'].lower(),  # "10:00am"
            class_info['time'].replace('am', ' am').replace('pm', ' pm').lower(),  # "10:00 am"
            class_info['time'].replace(':00', '').lower(),  # "10am"
        ]
        
        # Find all "Book" buttons on the page
        try:
            book_buttons = page.locator('button:has-text("Book"), button:has-text("BOOK")').all()
            print(f"  Found {len(book_buttons)} booking buttons on page")
            
            for button in book_buttons:
                try:
                    # Go up the parent tree to find the class card container
                    parent = button
                    for level in range(8):  # Try up to 8 levels
                        parent_elem = parent.locator('xpath=..').first
                        parent_text = parent_elem.inner_text().lower()
                        
                        # Check if this parent contains our class name AND time
                        has_class_name = (class_name_lower in parent_text or class_type_lower in parent_text)
                        has_correct_time = any(tv in parent_text for tv in time_variants)
                        
                        if has_class_name and has_correct_time:
                            # Additional validation: make sure it's a reasonable-sized class card
                            # (not the entire page body)
                            text_length = len(parent_text)
                            if 50 < text_length < 500:  # Class cards are typically 100-300 chars
                                # Final check: ensure no OTHER times appear before our target time
                                # This prevents matching a card that lists multiple classes
                                lines = parent_text.split('\n')
                                our_time_found = False
                                wrong_class = False
                                
                                for line in lines:
                                    # Check if this line has our target time
                                    if any(tv in line for tv in time_variants):
                                        # Check if our class name is near this time mention
                                        if class_name_lower in parent_text[max(0, parent_text.find(line)-100):parent_text.find(line)+200]:
                                            our_time_found = True
                                            break
                                
                                if our_time_found:
                                    print(f"  ✓ FOUND! {class_info['name']} at {class_info['time']}")
                                    print(f"    Card size: {text_length} chars")
                                    print(f"    Text preview: {parent_text[:150]}...")
                                    target_class = parent_elem
                                    break
                        
                        parent = parent_elem
                    
                    if target_class:
                        break
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"  Error finding book buttons: {str(e)}")
        
        if not target_class:
            print(f"Could not find class: {class_info['name']} at {class_info['time']}")
            print("Taking screenshot for debugging...")
            page.screenshot(path=f'error_class_not_found_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            return False
        
        # Look for "Book Now" button within the class container
        print("Looking for Book Now button...")
        try:
            book_button = target_class.locator('button:has-text("Book"), button:has-text("Reserve"), button:has-text("BOOK")').first
        except:
            # Try to find it in a broader context
            book_button = page.locator('button:has-text("Book Now"), button:has-text("Book"), button:has-text("Reserve"), button:has-text("BOOK")').first
        
        if not book_button:
            print("Class found but no Book button available (might be full or already booked)")
            page.screenshot(path=f'error_no_book_button_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            return False
        
        print("Clicking Book Now button...")
        # Scroll to the button first (human behavior)
        book_button.scroll_into_view_if_needed()
        human_delay(300, 600)
        random_mouse_movement(page)  # Move mouse around a bit
        human_click(book_button, page)
        
        # Wait for page to start loading
        print("Waiting for page to load after clicking Book Now...")
        human_delay(2000, 3000)
        
        # Wait for network to be idle (page fully loaded)
        try:
            page.wait_for_load_state('networkidle', timeout=15000)
            print("Page loaded successfully")
        except:
            print("Network idle timeout, continuing anyway...")
            page.wait_for_load_state('load', timeout=10000)
        
        # Additional delay to ensure everything is rendered
        human_delay(3000, 5000)
        
        # Check if we're being asked to login after clicking Book Now
        print(f"After clicking Book Now - Current URL: {page.url}")
        
        # Check if we're on a sign-in page
        if 'signin.mindbodyonline.com' in page.url or 'login' in page.url.lower():
            print("⚠️ Login required after clicking Book Now. Logging in...")
            
            try:
                # Wait for the page to fully load
                page.wait_for_load_state('load', timeout=10000)
                human_delay(2000, 3000)
                
                # Enter email
                print(f"Entering email: {config['email']}")
                email_input = page.wait_for_selector('input[type="email"], input[name="email"], input#email, input[id="EmailAddress"], input[placeholder*="email"]', timeout=10000)
                human_click(email_input, page)
                human_delay(200, 500)
                human_type(email_input, config['email'], page)
                human_delay(500, 1000)
                
                # Click continue
                print("Clicking continue button...")
                continue_button = page.wait_for_selector('button:has-text("Continue"), button[type="submit"], input[type="submit"]', timeout=10000)
                human_click(continue_button, page)
                human_delay(2000, 3000)
                
                # Enter password
                print("Entering password...")
                password_input = page.wait_for_selector('input[type="password"], input[name="password"], input[id="Password"]', timeout=10000)
                human_click(password_input, page)
                human_delay(200, 500)
                human_type(password_input, password, page)
                human_delay(500, 1000)
                
                # Submit
                print("Submitting login form...")
                submit_button = page.wait_for_selector('button[type="submit"], button:has-text("Sign in"), button:has-text("Log in"), input[type="submit"]', timeout=10000)
                human_click(submit_button, page)
                
                print("Waiting for authentication to complete...")
                page.wait_for_load_state('networkidle', timeout=30000)
                human_delay(3000, 5000)
                print(f"Login completed - New URL: {page.url}")
            except Exception as e:
                print(f"❌ Error during login after Book Now: {str(e)}")
                page.screenshot(path=f'error_login_after_book_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
                return False
        
        # Check for CAPTCHA and solve with 2captcha if detected
        print("Checking for CAPTCHA...")
        print(f"Current URL before CAPTCHA check: {page.url}")
        
        # Only check for CAPTCHA if we're not already on a booking/confirmation page
        current_url = page.url.lower()
        if 'book' in current_url or 'purchase' in current_url or 'checkout' in current_url or 'confirm' in current_url:
            print("On booking/checkout page, skipping CAPTCHA check")
        elif detect_captcha(page):
            print("⚠ CAPTCHA detected! Attempting to solve with 2captcha...")
            page.screenshot(path=f'captcha_detected_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            
            # Try to solve with 2captcha
            if not solve_recaptcha_v2(page, config):
                print("❌ Failed to solve CAPTCHA, going back to retry booking...")
                try:
                    page.go_back()
                    human_delay(2000, 3000)
                except:
                    pass
                return False  # Retry this booking
            
            print("✓ CAPTCHA solved successfully, continuing...")
        else:
            print("No CAPTCHA detected, proceeding...")
        
        print(f"Current URL after CAPTCHA check: {page.url}")
        
        # Wait for the Buy button page to load
        print("Waiting for Buy button...")
        try:
            buy_button = page.wait_for_selector('button:has-text("Buy"), button:has-text("Complete Purchase"), button:has-text("Confirm"), button:has-text("Complete"), button:has-text("Checkout")', timeout=15000)
            if buy_button:
                print(f"✓ Found Buy button! Text: {buy_button.inner_text()}")
                print("Clicking Buy button to complete booking...")
                # Scroll to button and move mouse naturally
                buy_button.scroll_into_view_if_needed()
                human_delay(500, 1000)
                random_mouse_movement(page)
                human_click(buy_button, page)
                
                # Wait for page to start processing
                print("Waiting for booking to process...")
                human_delay(3000, 4000)
                
                # Wait for network to be idle (booking processed)
                try:
                    page.wait_for_load_state('networkidle', timeout=15000)
                    print("Booking processed successfully")
                except:
                    print("Network idle timeout, continuing anyway...")
                    page.wait_for_load_state('load', timeout=10000)
                
                # Additional delay to ensure confirmation page is fully loaded
                human_delay(4000, 6000)
                print(f"After clicking Buy - Current URL: {page.url}")
            else:
                print("Buy button found but not visible")
                return False
        except PlaywrightTimeout:
            print("⚠️ Buy button not found within 15 seconds")
            print(f"Current URL: {page.url}")
            page.screenshot(path=f'no_buy_button_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            return False
        
        # CRITICAL: Check for CAPTCHA again after clicking Buy
        print("Checking for CAPTCHA after clicking Buy...")
        print(f"Current URL before CAPTCHA check: {page.url}")
        
        # Only check for CAPTCHA if we're not on a success/confirmation page
        current_url = page.url.lower()
        page_content = page.content().lower()
        
        # If we see success indicators, skip CAPTCHA check
        success_keywords = ['success', 'confirmed', 'thank', 'confirmation', 'you\'re all set']
        has_success = any(keyword in page_content or keyword in current_url for keyword in success_keywords)
        
        if has_success:
            print("Success page detected, skipping CAPTCHA check")
        elif detect_captcha(page):
            print("⚠ CAPTCHA detected after clicking Buy! Attempting to solve with 2captcha...")
            page.screenshot(path=f'captcha_after_buy_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            
            # Try to solve with 2captcha
            if not solve_recaptcha_v2(page, config):
                print("❌ Failed to solve CAPTCHA after Buy, going back to retry booking...")
                try:
                    page.go_back()
                    human_delay(2000, 3000)
                except:
                    pass
                return False  # Retry this booking
            
            print("✓ CAPTCHA solved successfully after Buy button, continuing...")
        else:
            print("No CAPTCHA detected after Buy button")
        
        # Handle any final confirmation dialogs
        try:
            confirm_button = page.wait_for_selector('button:has-text("Confirm"), button:has-text("Yes"), button:has-text("Done")', timeout=5000)
            if confirm_button:
                print("Clicking final confirmation button...")
                human_click(confirm_button, page)
                human_delay(2000, 3000)
        except:
            pass  # No additional confirmation needed
        
        # VERIFY THE BOOKING WAS SUCCESSFUL
        print("Verifying booking success...")
        human_delay(2000, 3000)
        
        # Take screenshot of final page
        page.screenshot(path=f'booking_result_{class_info["name"]}_{class_info["time"].replace(":", "")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        
        # Check for success indicators
        page_content = page.content().lower()
        page_url = page.url.lower()
        
        success_indicators = [
            'success',
            'confirmed',
            'reservation confirmed',
            'booking confirmed',
            'you\'re all set',
            'thanks',
            'thank you',
            'confirmation'
        ]
        
        failure_indicators = [
            'error',
            'failed',
            'unable to',
            'try again',
            'something went wrong'
        ]
        
        # Check for failure first
        for indicator in failure_indicators:
            if indicator in page_content:
                print(f"❌ Booking FAILED - Found failure indicator: '{indicator}'")
                return False
        
        # Check for success
        found_success = False
        for indicator in success_indicators:
            if indicator in page_content or indicator in page_url:
                print(f"✓ Booking SUCCESS - Found success indicator: '{indicator}'")
                found_success = True
                break
        
        if not found_success:
            print("⚠️ Could not verify booking success - no clear success indicator found")
            print(f"Final URL: {page.url}")
            # Consider this a failure to be safe
            return False
        
        print(f"✓ Successfully booked and VERIFIED: {class_info['name']} at {class_info['time']}")
        return True
        
    except Exception as e:
        print(f"Error during class booking: {str(e)}")
        print(traceback.format_exc())
        page.screenshot(path=f'error_booking_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        return False


def main():
    """Main execution function"""
    print("="*60)
    print("MindBody Auto Booking Script")
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("="*60)
    
    try:
        # Load configuration
        config = load_config()
        password = get_password()
        
        # Determine target classes
        booking_info = get_target_classes(config)
        if not booking_info:
            print("No booking scheduled for today. Exiting.")
            sys.exit(0)
        
        target_day = booking_info['target_day']
        classes = booking_info['classes']
        target_date = calculate_target_date(target_day)
        
        print(f"\nBooking {len(classes)} class(es) for {target_day}, {target_date.strftime('%B %d, %Y')}")
        
        # Start browser automation
        with sync_playwright() as p:
            # Launch with extra args to appear more human
            browser = p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            
            # Randomize viewport slightly
            viewport_width = random.randint(1900, 1920)
            viewport_height = random.randint(1040, 1080)
            
            context = browser.new_context(
                viewport={'width': viewport_width, 'height': viewport_height},
                user_agent=get_random_user_agent(),
                locale='en-US',
                timezone_id='America/Toronto',
                permissions=['geolocation'],
                geolocation={'latitude': 45.5017, 'longitude': -73.5673},  # Montreal
            )
            
            page = context.new_page()
            
            # Inject stealth scripts
            page.add_init_script(get_stealth_scripts())
            
            # Login once
            login(page, config, password)
            
            # Book each class
            results = []
            for class_info in classes:
                try:
                    success = book_class(page, config, class_info, target_date, password)
                    results.append({
                        'class': class_info,
                        'success': success
                    })
                    
                    # Wait between bookings to avoid rate limiting
                    if len(classes) > 1:
                        human_delay(3000, 5000)
                except Exception as e:
                    print(f"Error booking {class_info['name']}: {str(e)}")
                    results.append({
                        'class': class_info,
                        'success': False
                    })
            
            # Summary
            print("\n" + "="*60)
            print("BOOKING SUMMARY")
            print("="*60)
            for result in results:
                status = "✓ SUCCESS" if result['success'] else "✗ FAILED"
                print(f"{status}: {result['class']['name']} at {result['class']['time']}")
            print("="*60)
            
            browser.close()
        
        # Exit with appropriate code
        all_success = all(r['success'] for r in results)
        sys.exit(0 if all_success else 1)
        
    except Exception as e:
        print(f"\n{'='*60}")
        print("CRITICAL ERROR")
        print("="*60)
        print(str(e))
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()


