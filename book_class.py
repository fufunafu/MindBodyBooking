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
    else:
        print(f"Not a booking day (today is {day_name}). Script should run on Friday or Saturday.")
        return None


def calculate_target_date(target_day):
    """Calculate the target date for booking"""
    today = datetime.now()
    days_ahead = {'saturday': 5, 'sunday': 6, 'monday': 0, 'tuesday': 1, 
                  'wednesday': 2, 'thursday': 3, 'friday': 4}
    
    target_day_lower = target_day.lower()
    current_weekday = today.weekday()  # Monday is 0, Sunday is 6
    
    if target_day_lower == 'saturday':
        days_to_add = (5 - current_weekday) % 7
        if days_to_add == 0:
            days_to_add = 7  # If today is Saturday, book next Saturday
    elif target_day_lower == 'sunday':
        days_to_add = (6 - current_weekday) % 7
        if days_to_add == 0:
            days_to_add = 7  # If today is Sunday, book next Sunday
    else:
        days_to_add = 1  # Default to tomorrow
    
    target_date = today + timedelta(days=days_to_add)
    return target_date


def login(page, config, password):
    """Handle login flow"""
    print("Navigating to sign-in page...")
    page.goto(config['signin_url'], wait_until='networkidle', timeout=60000)
    
    print(f"Entering email: {config['email']}")
    email_input = page.wait_for_selector('input[type="email"], input[name="email"], input#email', timeout=10000)
    email_input.fill(config['email'])
    
    print("Clicking continue button...")
    continue_button = page.wait_for_selector('button:has-text("Continue"), button[type="submit"]', timeout=10000)
    continue_button.click()
    
    print("Entering password...")
    password_input = page.wait_for_selector('input[type="password"], input[name="password"]', timeout=10000)
    password_input.fill(password)
    
    print("Submitting login form...")
    submit_button = page.wait_for_selector('button[type="submit"], button:has-text("Sign in"), button:has-text("Log in")', timeout=10000)
    submit_button.click()
    
    print("Waiting for authentication to complete...")
    page.wait_for_load_state('networkidle', timeout=30000)
    print("Login successful!")


def book_class(page, config, class_info, target_date):
    """Book a specific class"""
    print(f"\n{'='*60}")
    print(f"Attempting to book: {class_info['name']} at {class_info['time']}")
    print(f"Target date: {target_date.strftime('%A, %B %d, %Y')}")
    print(f"{'='*60}\n")
    
    # Navigate to studio page
    print("Navigating to Studio Locomotion page...")
    page.goto(config['studio_url'], wait_until='networkidle', timeout=60000)
    page.wait_for_timeout(3000)  # Wait for page to fully load
    
    # Format date for searching
    target_day = target_date.strftime('%d')  # Day of month
    target_month = target_date.strftime('%B')  # Full month name
    
    print(f"Looking for date: {target_month} {target_day}")
    
    # Find and click the target date
    # Try multiple selectors for date buttons
    date_selectors = [
        f'button:has-text("{target_day}")',
        f'div[role="button"]:has-text("{target_day}")',
        f'[data-date*="{target_date.strftime("%Y-%m-%d")}"]',
        f'button[aria-label*="{target_month} {target_day}"]'
    ]
    
    date_button = None
    for selector in date_selectors:
        try:
            date_button = page.wait_for_selector(selector, timeout=5000)
            if date_button:
                print(f"Found date using selector: {selector}")
                break
        except:
            continue
    
    if not date_button:
        print(f"Could not find date button for {target_month} {target_day}")
        print("Taking screenshot for debugging...")
        page.screenshot(path=f'error_date_not_found_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        return False
    
    print("Clicking on target date...")
    date_button.click()
    page.wait_for_timeout(2000)
    
    # Find the specific class
    print(f"Searching for class: {class_info['name']} at {class_info['time']}")
    
    # Look for class card containing the time and name
    time_str = class_info['time'].lower().replace('am', '').replace('pm', '').strip()
    
    # Try to find class elements
    try:
        # Wait for classes to load
        page.wait_for_selector('[class*="class"], [data-testid*="class"], .schedule-item', timeout=10000)
        page.wait_for_timeout(2000)
        
        # Get all potential class containers
        class_containers = page.query_selector_all('[class*="class"], [data-testid*="class"], .schedule-item, [role="article"]')
        
        print(f"Found {len(class_containers)} potential class containers")
        
        target_class = None
        for container in class_containers:
            text_content = container.inner_text().lower()
            
            # Check if this container has the right time
            if class_info['time'].lower() in text_content or time_str in text_content:
                print(f"Found class at {class_info['time']}")
                
                # Check if it matches the class name or type
                class_name_lower = class_info['name'].lower()
                class_type_lower = class_info['type'].lower()
                
                if class_name_lower in text_content or class_type_lower in text_content:
                    print(f"Confirmed class match: {class_info['name']}")
                    target_class = container
                    break
        
        if not target_class:
            print(f"Could not find class: {class_info['name']} at {class_info['time']}")
            print("Taking screenshot for debugging...")
            page.screenshot(path=f'error_class_not_found_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            return False
        
        # Look for "Book Now" button within the class container
        print("Looking for Book Now button...")
        book_button = target_class.query_selector('button:has-text("Book"), button:has-text("Reserve"), a:has-text("Book")')
        
        if not book_button:
            # Try to find it in a broader context
            book_button = page.query_selector('button:has-text("Book Now"), button:has-text("Book"), button:has-text("Reserve")')
        
        if not book_button:
            print("Class found but no Book button available (might be full or already booked)")
            page.screenshot(path=f'error_no_book_button_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            return False
        
        print("Clicking Book Now button...")
        book_button.click()
        page.wait_for_timeout(2000)
        
        # Handle any confirmation dialogs
        try:
            confirm_button = page.wait_for_selector('button:has-text("Confirm"), button:has-text("Yes"), button:has-text("Complete")', timeout=5000)
            if confirm_button:
                print("Clicking confirmation button...")
                confirm_button.click()
                page.wait_for_timeout(2000)
        except:
            pass  # No confirmation needed
        
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


