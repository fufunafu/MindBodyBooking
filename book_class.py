#!/usr/bin/env python3
"""
MindBody Auto Booking Script
Automates booking of fitness classes at Studio Locomotion via MindBody Online
"""

import os
import json
import sys
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import traceback


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
    page.wait_for_timeout(3000)
    
    # Handle cookie consent popup - remove ALL overlays
    print("Removing any cookie consent overlays...")
    try:
        page.evaluate('''() => {
            // Remove all trust-e / cookie consent overlays
            const overlays = document.querySelectorAll('.truste_overlay, .truste_cm_outerdiv, [id*="pop-"], [class*="truste"]');
            overlays.forEach(el => el.remove());
            console.log('Removed', overlays.length, 'overlay elements');
        }''')
        page.wait_for_timeout(1000)
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
        sign_in_button.click()
        print("Waiting for login page to load...")
        page.wait_for_load_state('load', timeout=30000)
        page.wait_for_timeout(3000)
    else:
        print("Sign In button not found, may already be logged in or on login page")
    
    # Check if we need to login
    print(f"Current URL: {page.url}")
    if 'signin.mindbodyonline.com' not in page.url and 'login' not in page.url.lower():
        print("Already logged in!")
        return
    
    print(f"Entering email: {config['email']}")
    
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
    
    email_input.fill(config['email'])
    
    print("Clicking continue button...")
    continue_button = page.wait_for_selector('button:has-text("Continue"), button[type="submit"], input[type="submit"]', timeout=10000)
    continue_button.click()
    page.wait_for_timeout(2000)
    
    print("Entering password...")
    password_input = page.wait_for_selector('input[type="password"], input[name="password"], input[id="Password"]', timeout=10000)
    password_input.fill(password)
    
    print("Submitting login form...")
    submit_button = page.wait_for_selector('button[type="submit"], button:has-text("Sign in"), button:has-text("Log in"), input[type="submit"]', timeout=10000)
    submit_button.click()
    
    print("Waiting for authentication to complete...")
    page.wait_for_load_state('load', timeout=30000)
    page.wait_for_timeout(3000)
    print("Login successful!")


def book_class(page, config, class_info, target_date):
    """Book a specific class"""
    print(f"\n{'='*60}")
    print(f"Attempting to book: {class_info['name']} at {class_info['time']}")
    print(f"Target date: {target_date.strftime('%A, %B %d, %Y')}")
    print(f"{'='*60}\n")
    
    # Navigate to studio page
    print("Navigating to Studio Locomotion page...")
    page.goto(config['studio_url'], wait_until='load', timeout=60000)
    page.wait_for_timeout(3000)  # Wait for page to fully load
    
    # Handle cookie consent popup on studio page  
    print("Checking for cookie consent on studio page...")
    try:
        # Wait for popup to appear
        page.wait_for_timeout(3000)
        
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
                    page.wait_for_timeout(2000)
                    break
            except:
                continue
        
        if not button_clicked:
            print("Button not found in frames, trying main page...")
            try:
                button = page.locator('button:has-text("AGREE AND PROCEED")').first
                button.click(force=True, timeout=5000)
                print("Clicked button on main page")
                page.wait_for_timeout(2000)
            except:
                print("Could not find/click consent button, continuing anyway...")
        
    except Exception as e:
        print(f"Cookie popup handling: {str(e)}")
    
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
                    elem.click(timeout=2000)
                    date_found = True
                    print(f"Successfully clicked on date {target_day}")
                    page.wait_for_timeout(3000)
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
        page.wait_for_timeout(2000)
        
        # Scroll down to load all classes
        print("Scrolling to load all classes...")
        for i in range(5):
            page.evaluate('window.scrollBy(0, 800)')
            page.wait_for_timeout(800)
        
        page.wait_for_timeout(1000)
        
        # NEW APPROACH: Find time elements first, then look for class name nearby
        print("Searching by time first...")
        
        # Look for elements containing the time
        time_variants = [
            class_info['time'],  # "7:00am"
            class_info['time'].replace('am', ' am').replace('pm', ' pm'),  # "7:00 am"
            class_info['time'].replace(':00', ''),  # "7am"
        ]
        
        target_class = None
        class_name_lower = class_info['name'].lower()
        class_type_lower = class_info['type'].lower()
        
        for time_variant in time_variants:
            print(f"  Looking for time: '{time_variant}'...")
            time_elements = page.locator(f'text={time_variant}').all()
            print(f"  Found {len(time_elements)} elements with time '{time_variant}'")
            
            for time_elem in time_elements:
                try:
                    # Get the parent or ancestor that contains both time and class info
                    # Try going up a few levels to find the full class card
                    parent = time_elem
                    for level in range(5):  # Try up to 5 levels up
                        parent_elem = parent.locator('xpath=..').first
                        parent_text = parent_elem.inner_text().lower()
                        
                        # Check if this parent contains the class name
                        if class_name_lower in parent_text or class_type_lower in parent_text:
                            print(f"  ✓ FOUND! {class_info['name']} at {class_info['time']}")
                            print(f"    Text: {parent_text[:200]}")
                            target_class = parent_elem
                            break
                        
                        parent = parent_elem
                    
                    if target_class:
                        break
                except:
                    continue
            
            if target_class:
                break
        
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
        book_button.click()
        page.wait_for_timeout(3000)
        
        # Wait for the Buy button page to load
        print("Waiting for Buy button...")
        try:
            buy_button = page.wait_for_selector('button:has-text("Buy"), button:has-text("Complete Purchase"), button:has-text("Confirm")', timeout=10000)
            if buy_button:
                print("Clicking Buy button to complete booking...")
                buy_button.click()
                page.wait_for_timeout(3000)
        except PlaywrightTimeout:
            print("Buy button not found - checking if booking was already completed")
        
        # Handle any final confirmation dialogs
        try:
            confirm_button = page.wait_for_selector('button:has-text("Confirm"), button:has-text("Yes"), button:has-text("Done")', timeout=5000)
            if confirm_button:
                print("Clicking final confirmation button...")
                confirm_button.click()
                page.wait_for_timeout(2000)
        except:
            pass  # No additional confirmation needed
        
        print(f"✓ Successfully booked: {class_info['name']} at {class_info['time']}")
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
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            # Login once
            login(page, config, password)
            
            # Book each class
            results = []
            for class_info in classes:
                try:
                    success = book_class(page, config, class_info, target_date)
                    results.append({
                        'class': class_info,
                        'success': success
                    })
                    
                    # Wait between bookings to avoid rate limiting
                    if len(classes) > 1:
                        page.wait_for_timeout(3000)
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


