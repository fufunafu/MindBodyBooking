# MindBody Auto Booking System

Automated class booking system for Studio Locomotion classes via MindBody Online. This system automatically books your weekly fitness classes at 5 AM on Fridays and Saturdays using GitHub Actions.

## Overview

This automation script:
- Logs into your MindBody account automatically
- Books specific classes at Studio Locomotion
- Runs in the cloud (no need to keep your computer on)
- Books 2 classes each run (4 classes total per week)

### Booking Schedule

**Friday 5:00 AM EST** → Books Saturday classes:
- 9:30 AM: Weight training (Athlétique)
- 11:30 AM: Weight training (Athlétique)

**Saturday 5:00 AM EST** → Books Sunday classes:
- 9:30 AM: Weight training (Athlétique)
- 11:30 AM: Strength training (Composition)

## Features

- ✅ Fully automated cloud-based booking
- ✅ No manual intervention required
- ✅ Runs even when your computer is off
- ✅ Error screenshots for debugging
- ✅ Secure credential storage with GitHub Secrets
- ✅ Detailed logging for each booking attempt
- ✅ Manual trigger option for testing

## Quick Start

### Prerequisites

- GitHub account (free)
- MindBody account with Studio Locomotion access
- Basic familiarity with Git and GitHub

### Installation

1. **Clone or create this repository**
   ```bash
   git clone <your-repo-url>
   cd MindBodyBooking
   ```

2. **Push to GitHub** (if not already there)
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/MindBodyBooking.git
   git push -u origin main
   ```

3. **Add your password as a GitHub Secret**
   - Go to repository **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `MINDBODY_PASSWORD`
   - Value: Your MindBody password
   - Click **Add secret**

4. **Enable GitHub Actions**
   - Go to **Actions** tab
   - Enable workflows if prompted

5. **Test the setup**
   - Go to **Actions** tab
   - Click **MindBody Auto Booking**
   - Click **Run workflow** → **Run workflow**
   - Monitor the execution

That's it! The system will now run automatically every Friday and Saturday at 5 AM EST.

## Project Structure

```
MindBodyBooking/
├── .github/
│   └── workflows/
│       └── schedule-booking.yml    # GitHub Actions workflow
├── book_class.py                   # Main booking script
├── config.json                     # Configuration (classes, URLs)
├── requirements.txt                # Python dependencies
├── SETUP.md                        # Detailed setup guide
└── README.md                       # This file
```

## Configuration

### Modifying Class Schedule

Edit `config.json` to change which classes to book:

```json
{
  "booking_schedule": {
    "friday": {
      "target_day": "Saturday",
      "classes": [
        {
          "time": "9:30am",
          "type": "Weight training",
          "name": "Athlétique"
        }
      ]
    }
  }
}
```

### Changing Run Times

Edit `.github/workflows/schedule-booking.yml`:

```yaml
schedule:
  - cron: '0 10 * * 5,6'  # 10 AM UTC = 5 AM EST
```

Use [crontab.guru](https://crontab.guru/) to help generate cron schedules.

## How It Works

### Technology Stack

- **Python 3.11**: Core programming language
- **Playwright**: Browser automation (headless Chrome)
- **GitHub Actions**: Cloud scheduler and runner
- **GitHub Secrets**: Secure credential storage

### Workflow

1. GitHub Actions triggers at scheduled time
2. Workflow provisions Ubuntu VM in the cloud
3. Installs Python, Playwright, and dependencies
4. Runs `book_class.py` with your credentials
5. Script logs into MindBody
6. Navigates to Studio Locomotion
7. Finds and books the specified classes
8. Captures screenshots if errors occur
9. VM shuts down automatically

### Authentication Flow

1. Navigate to MindBody sign-in page
2. Enter email address
3. Click Continue
4. Enter password (from GitHub Secret)
5. Submit and wait for redirect
6. Proceed to booking

### Booking Logic

1. Determine current day (Friday or Saturday)
2. Calculate target date (Saturday or Sunday)
3. Navigate to studio page
4. Click on target date
5. For each class:
   - Find class by time and name
   - Click "Book Now" button
   - Handle confirmation if needed
6. Report results

## Monitoring & Troubleshooting

### Check Booking Status

1. Go to **Actions** tab in your GitHub repository
2. View recent workflow runs
3. Green checkmark = success, Red X = failure

### View Logs

Click on any workflow run to see detailed logs:
- Authentication steps
- Date and class finding
- Booking confirmations
- Error messages

### Error Screenshots

If booking fails, error screenshots are saved:
1. Go to failed workflow run
2. Scroll to bottom
3. Download **error-screenshots** artifact
4. Unzip and view PNG files

### Common Issues

**Issue**: Workflow doesn't run at scheduled time
- **Solution**: Ensure GitHub Actions is enabled; check repository is not archived

**Issue**: "Class not found"
- **Solution**: Verify class name/time in `config.json`; check if class schedule changed

**Issue**: "No Book button available"
- **Solution**: Class might be full or already booked

**Issue**: Login fails
- **Solution**: Verify password in GitHub Secrets is correct

## Local Testing

For development or testing:

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Set password
export MINDBODY_PASSWORD="your_password"

# Run script
python book_class.py
```

**Note**: Script only runs on Friday/Saturday. For other days, modify `get_target_classes()` function temporarily.

## Cost

**Free!** GitHub Actions provides:
- 2,000 minutes/month for free accounts
- This script uses ~2-5 minutes per run
- 8 runs/month = ~40 minutes total
- Well within free tier limits

## Security

- Password stored as encrypted GitHub Secret
- Never exposed in logs or screenshots
- Only accessible during workflow execution
- Repository should be private for extra security

## Updates & Maintenance

### Update Password

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click on `MINDBODY_PASSWORD`
3. Update and save

### Update Class Schedule

1. Edit `config.json`
2. Commit and push changes
3. Changes take effect on next run

### Disable Automation

1. Go to **Actions** tab
2. Click **MindBody Auto Booking**
3. Click ⋯ menu → **Disable workflow**

## Support

For issues:
1. Check workflow logs in Actions tab
2. Review error screenshots
3. Verify configuration in `config.json`
4. Test locally if possible

## License

MIT License - Feel free to use and modify for your needs.

## Testing Results

✅ **Successfully tested on November 23, 2025**
- Login: Successful
- Cookie consent handling: Working
- Date selection: Working
- Class finding: Working  
- Booking flow (Book Now → Buy): Working
- Test class booked: Monday 7:00 AM Athlétique with Patricia Houde

## Disclaimer

This tool is for personal use. Ensure automated booking complies with Studio Locomotion's and MindBody's terms of service. Use responsibly.

