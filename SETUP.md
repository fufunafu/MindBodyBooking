# Setup Instructions

## Adding GitHub Secrets

To securely store your MindBody password, you need to add it as a GitHub Secret:

### Step-by-Step Guide

1. **Push this repository to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: MindBody auto booking system"
   git branch -M main
   git remote add origin https://github.com/fufunafu/MindBodyBooking.git
   git push -u origin main
   ```

2. **Navigate to Repository Settings**
   - Go to your repository on GitHub
   - Click on **Settings** tab
   - In the left sidebar, click **Secrets and variables** → **Actions**

3. **Add New Secret**
   - Click the **New repository secret** button
   - Name: `MINDBODY_PASSWORD`
   - Value: `Tocson2509`
   - Click **Add secret**

4. **Enable GitHub Actions**
   - Go to the **Actions** tab in your repository
   - If prompted, click **I understand my workflows, go ahead and enable them**

5. **Test the Workflow**
   - Go to **Actions** tab
   - Select **MindBody Auto Booking** workflow
   - Click **Run workflow** button (manual trigger)
   - Select `main` branch and click **Run workflow**
   - Monitor the execution to ensure it works correctly

## Local Testing (Optional)

Before deploying, you can test the script locally:

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Set environment variable**
   ```bash
   export MINDBODY_PASSWORD="Tocson2509"
   ```

3. **Run the script**
   ```bash
   python book_class.py
   ```

   Note: The script only runs on Friday or Saturday. To test on other days, you can temporarily modify the `get_target_classes()` function.

## Schedule Details

The workflow runs automatically:
- **Friday at 5:00 AM EST**: Books Saturday 9:30 AM and 11:30 AM classes
- **Saturday at 5:00 AM EST**: Books Sunday 9:30 AM and 11:30 AM classes

The schedule is defined in `.github/workflows/schedule-booking.yml` using cron syntax:
```yaml
schedule:
  - cron: '0 10 * * 5,6'  # 10 AM UTC = 5 AM EST
```

## Monitoring

### Check Workflow Runs
1. Go to **Actions** tab in your repository
2. View the history of automated runs
3. Click on any run to see detailed logs

### View Error Screenshots
If a booking fails:
1. Go to the failed workflow run
2. Scroll to the bottom of the page
3. Download the **error-screenshots** artifact
4. Examine the screenshots to diagnose the issue

## Troubleshooting

### Workflow Not Running
- Ensure GitHub Actions is enabled in your repository
- Check that the repository is not archived
- Verify the schedule syntax in the workflow file

### Booking Fails
- Check if your MindBody credentials are correct
- Verify that classes are available at the specified times
- Review error screenshots for clues
- Check workflow logs for detailed error messages

### Update Password
If you need to change your password:
1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Click on `MINDBODY_PASSWORD`
3. Click **Update secret**
4. Enter new password and save

## Security Notes

- Never commit your password in code or configuration files
- Keep your repository private if possible
- GitHub Secrets are encrypted and only exposed during workflow runs
- The password is not visible in logs or to other users

