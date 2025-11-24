# Anti-Bot Detection Features

This document outlines all the anti-bot detection measures implemented in the MindBody booking script.

## 1. Browser Fingerprint Masking

### WebDriver Detection Prevention
- Overrides `navigator.webdriver` property to return `undefined` instead of `true`
- Removes automation-controlled browser features

### User Agent Randomization
- Rotates between 5 realistic user agents (Chrome on Mac/Windows, Safari)
- Changes on each run to avoid patterns

### Canvas Fingerprinting Protection
- Adds subtle random noise to canvas pixel data
- Prevents websites from creating unique canvas fingerprints

### WebGL Fingerprinting Protection
- Randomizes WebGL renderer and vendor strings
- Returns consistent but non-bot GPU information

### Browser Property Spoofing
- Adds realistic `window.chrome` object
- Populates `navigator.plugins` array
- Customizes permissions API responses

## 2. Human-Like Mouse Behavior

### Curved Mouse Movement
- Implements Bezier curves for natural mouse paths
- Adds random control points for realistic trajectories
- Includes micro-jitter at destination (humans aren't perfectly precise)

### Random Mouse Movement
- Simulates browsing behavior with random mouse movements
- Moves mouse around the page naturally between actions
- Varies movement patterns (1-3 movements)

### Off-Center Clicking
- Clicks are slightly off-center (±5px) from element center
- Mimics human imprecision

## 3. Human-Like Typing

### Variable Typing Speed
- Random delays between keystrokes (50-200ms)
- Occasional longer pauses (200-500ms) simulating thinking

### Realistic Typos
- 5% chance of making a typo and correcting it
- Presses backspace and retypes correctly
- Adds natural hesitation after mistakes

## 4. Human-Like Scrolling

### Chunked Scrolling
- Breaks scroll into 3-6 smaller chunks
- Adds pauses between chunks (50-150ms)

### Scroll-Back Behavior
- 30% chance of scrolling back slightly after scrolling
- Mimics humans who overshoot and correct

### Random Scroll Amounts
- Varies scroll distance (300-800px typical)
- Not fixed, robotic amounts

## 5. Idle Behaviors

### Reading Simulation
- Random tiny scrolls (as if following text with eyes)
- Mouse wiggling while "reading"
- Random pauses (0.5-1.5s)
- Scroll down and back up (checking something)

### Strategic Placement
- After page loads
- While waiting for elements
- Between major actions

## 6. Timing Variations

### Human Delays
- All delays are randomized within ranges
- Short delays: 1000-3000ms
- Medium delays: 2000-4000ms
- Long delays: 3000-5000ms

### Action Delays
- Pauses before clicking (50-150ms)
- Pauses after clicking (100-250ms)
- Pauses before typing (200-500ms)

## 7. Browser Configuration

### Launch Arguments
- `--disable-blink-features=AutomationControlled` - Hides automation
- `--disable-dev-shm-usage` - More stable
- `--no-sandbox` - Avoids sandbox detection
- `--disable-web-security` - Prevents CORS issues
- `--disable-features=IsolateOrigins,site-per-process` - Reduces fingerprinting

### Viewport Randomization
- Width: 1900-1920px (random)
- Height: 1040-1080px (random)
- Prevents fixed viewport fingerprinting

### Geolocation
- Sets realistic location (Montreal)
- Adds geolocation permissions

### Locale & Timezone
- Sets locale to `en-US`
- Sets timezone to `America/Toronto`
- Matches expected user location

## 8. Interaction Improvements

### Element Preparation
- Scrolls elements into view before interacting
- Waits for visibility
- Adds hover before click

### Natural Flow
- Random mouse movements between actions
- Idle behaviors while "reading"
- Variable timing between steps

## 9. Pattern Avoidance

### No Fixed Patterns
- All timings are randomized
- No predictable sequences
- Behavior varies between runs

### Realistic Variance
- Different scroll amounts
- Different mouse paths
- Different typing speeds
- Different pause durations

## 10. Error Handling

### Graceful Fallbacks
- If human-like interaction fails, falls back to standard Playwright
- Non-critical errors don't break the flow
- Continues operation smoothly

---

## Testing Recommendations

When testing, look for:
1. ✅ Mouse follows curved paths, not straight lines
2. ✅ Typing has variable speed, occasional pauses
3. ✅ Random micro-movements between actions
4. ✅ Scroll happens in chunks, not instantly
5. ✅ Occasional "reading" behaviors (small scrolls, pauses)
6. ✅ No `navigator.webdriver` property visible
7. ✅ Canvas fingerprint changes between runs
8. ✅ Realistic user agent and browser properties

## Detection Resistance Level

**HIGH** - This implementation includes:
- ✅ All major webdriver detection bypasses
- ✅ Multiple layers of fingerprint randomization
- ✅ Comprehensive human behavior simulation
- ✅ Pattern avoidance through randomization
- ✅ Natural timing and interactions

The combination of these features makes the automation very difficult to distinguish from human behavior using standard bot detection techniques.

