# 📮 GitHub Automatic Telegram Quiz Poster

Automatically post quizzes to Telegram using GitHub Actions. Quizzes are posted from a Word document on a schedule!

## ✨ Features

✅ **Automatic scheduling** - Posts at specific time every day
✅ **Upload document** - Update quizzes.docx and it posts automatically  
✅ **No server needed** - Runs free on GitHub
✅ **Manual trigger** - Post anytime with custom time & delay
✅ **GitHub native** - Integrated directly into your repository

---

## 📋 Setup Guide

### Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com)
2. Click **+ New repository**
3. Name it: `telegram-quiz-bot`
4. Select **Public** or **Private**
5. Click **Create repository**

### Step 2: Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/telegram-quiz-bot.git
cd telegram-quiz-bot
```

### Step 3: Add Files to Repository

Copy these files to your local repository:

```
telegram-quiz-bot/
├── quizzes.docx                    (Your quiz file)
├── telegram_native_scheduler.py    (Scheduler script)
├── requirements.txt                (Python dependencies)
├── .gitignore                      (Ignore local files)
└── .github/
    └── workflows/
        └── post-quizzes.yml        (GitHub Actions workflow)
```

### Step 4: Create requirements.txt

Create a file named `requirements.txt`:

```
python-telegram-bot==20.0
httpx==0.24.0
python-docx==0.8.11
```

### Step 5: Create .gitignore

Create a file named `.gitignore`:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/

# IDE
.vscode/
.idea/

# Local
config.json
.env
```

### Step 6: Get Telegram Credentials

#### Get Bot Token:
1. Chat with [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot`
3. Follow instructions
4. Copy the **Bot Token** (looks like: `123456:ABC-DEF1234ghIkl`)

#### Get Chat ID:
1. Add bot to your group
2. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
3. Find `"chat":{"id":<YOUR_CHAT_ID>`
4. Copy the Chat ID (usually negative like `-1001234567890`)

### Step 7: Add Secrets to GitHub

1. Go to your repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

Add two secrets:

| Name | Value |
|------|-------|
| `TELEGRAM_BOT_TOKEN` | Your bot token (123456:ABC-DEF...) |
| `TELEGRAM_CHAT_ID` | Your chat ID (-1001234567890) |

✅ **Important:** These are private and won't show in logs!

### Step 8: Create Workflow File

Create folder structure:
```bash
mkdir -p .github/workflows
```

Create `.github/workflows/post-quizzes.yml` with the workflow code provided.

### Step 9: Push to GitHub

```bash
git add .
git commit -m "Setup automatic Telegram quiz posting"
git push origin main
```

---

## 📄 Quiz Document Format

Create a Word document `quizzes.docx` with this format:

```
Question: What is 2+2?
(a) 3
(b) 4
(c) 5
(d) 6
Ans: b
Explanation: 2 + 2 equals 4.

Question: What is the capital of France?
(a) London
(b) Paris
(c) Berlin
(d) Madrid
Ans: b
Explanation: Paris is the capital of France.
```

**Rules:**
- Start with `Question:`
- Use `(a)`, `(b)`, `(c)`, `(d)` for options
- End with `Ans:` + letter
- Everything after `Ans:` is ignored
- LaTeX/tables/images are auto-skipped

---

## ⏰ Scheduling Options

### Daily at Specific Time

Edit `.github/workflows/post-quizzes.yml`:

```yaml
schedule:
  - cron: '0 10 * * *'  # 10 AM UTC every day
  - cron: '0 14 * * *'  # 2 PM UTC every day
  - cron: '0 0 * * 1'   # Monday midnight UTC
```

### Cron Format

```
minute hour day month weekday

Examples:
0 10 * * *    - 10:00 AM UTC daily
0 14 * * *    - 2:00 PM UTC daily
0 9 * * 1-5   - 9:00 AM UTC Mon-Fri
0 0 1 * *     - Midnight on 1st of month
0 */6 * * *   - Every 6 hours
```

[Cron Schedule Helper](https://crontab.guru/)

---

## 🚀 How It Works

### Automatic (Schedule)
```
1. Every day at set time (e.g., 10 AM UTC)
   ↓
2. GitHub Actions runs automatically
   ↓
3. Reads quizzes.docx
   ↓
4. Posts to Telegram
   ↓
5. Done! ✅
```

### Manual (Workflow Dispatch)
```
1. Go to Actions tab
   ↓
2. Click "Post Telegram Quizzes"
   ↓
3. Click "Run workflow"
   ↓
4. Set custom time & delay
   ↓
5. Quizzes posted! ✅
```

### On File Upload
```
1. Update quizzes.docx
   ↓
2. Push to GitHub
   ↓
3. Workflow triggers automatically
   ↓
4. Posts new quizzes
   ↓
5. Done! ✅
```

---

## 📊 Monitor Workflow

1. Go to **Actions** tab in GitHub
2. Click "📮 Post Telegram Quizzes"
3. See all workflow runs
4. Click run to see logs

### Logs Show:
```
✅ Checked quiz file exists
📂 Reading: quizzes.docx
✅ Found 5 questions
📋 Valid quizzes: 5, Skipped: 0
⏰ Scheduling 5 quizzes
✅ Q1: Scheduled for 2024-05-20 10:00:00
✅ Q2: Scheduled for 2024-05-20 10:01:00
...
🎉 All quizzes have been sent!
```

---

## 🎮 Manual Trigger (Workflow Dispatch)

### From GitHub Web:
1. Go to **Actions** tab
2. Click **"📮 Post Telegram Quizzes"**
3. Click **"Run workflow"**
4. Enter custom options:
   - Schedule time (HH:MM, e.g., 14:30)
   - Delay between quizzes (minutes)
5. Click **"Run workflow"**

### From Command Line:
```bash
gh workflow run post-quizzes.yml \
  -f schedule_time="14:30" \
  -f delay_minutes="2"
```

---

## 📂 Repository Structure

```
telegram-quiz-bot/
│
├── quizzes.docx                    # Your quiz file
├── telegram_native_scheduler.py    # Scheduler code
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore rules
│
└── .github/
    └── workflows/
        └── post-quizzes.yml        # GitHub Actions workflow
```

---

## 🔐 Security

### Secrets Protection:
✅ Bot token hidden in GitHub secrets
✅ Chat ID hidden in GitHub secrets
✅ Never shown in logs
✅ Only accessible in workflow

### Best Practices:
- ✅ Use separate bot for each project
- ✅ Rotate tokens periodically
- ✅ Don't commit secrets to git
- ✅ Use `.gitignore` for local files

---

## 🆘 Troubleshooting

### Workflow Won't Run

**Solution:**
1. Check **Settings** → **Actions** → **General**
2. Enable "Allow all actions and reusable workflows"

### Bot Token Error

**Solution:**
1. Copy token again from @BotFather
2. Update in **Settings** → **Secrets**
3. Re-run workflow

### Chat ID Error

**Solution:**
1. Get Chat ID: `https://api.telegram.org/bot<TOKEN>/getUpdates`
2. Use negative number: `-1001234567890`
3. Make sure bot is in group

### File Not Found

**Solution:**
1. Ensure `quizzes.docx` is in root directory
2. Push file to GitHub: `git add quizzes.docx && git commit -m "Add quizzes" && git push`

### No Quizzes Found

**Solution:**
1. Check document format matches example
2. Ensure questions start with `Question:`
3. Verify options are `(a)`, `(b)`, `(c)`, `(d)`
4. Check answer line: `Ans: a/b/c/d`

---

## 📈 Advanced Configuration

### Post to Multiple Groups

Edit workflow:
```yaml
env:
  CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }},${{ secrets.TELEGRAM_CHAT_ID_2 }}
```

### Custom Explanation

Edit workflow:
```yaml
EXPLANATION: "Check the correct answer"
```

### Change Time Format

Edit workflow:
```yaml
# From 24-hour to 12-hour
'0 22 * * *'  # 10 PM UTC (22:00)
'0 02 * * *'  # 2 AM UTC (02:00)
```

---

## 📚 Files Needed

1. **quizzes.docx** - Your quiz file
2. **telegram_native_scheduler.py** - Scheduler code
3. **requirements.txt** - Dependencies
4. **.github/workflows/post-quizzes.yml** - Workflow file
5. **.gitignore** - Git rules

---

## ✅ Checklist

- [ ] Created GitHub repository
- [ ] Cloned repository locally
- [ ] Created quizzes.docx
- [ ] Got Bot Token from @BotFather
- [ ] Got Chat ID from Telegram API
- [ ] Added TELEGRAM_BOT_TOKEN to secrets
- [ ] Added TELEGRAM_CHAT_ID to secrets
- [ ] Created workflow file: `.github/workflows/post-quizzes.yml`
- [ ] Created requirements.txt
- [ ] Created .gitignore
- [ ] Copied scheduler script
- [ ] Pushed all files to GitHub
- [ ] Verified workflow runs in Actions tab

---

## 🎉 You're Done!

Your Telegram quizzes will now post automatically!

**Next Steps:**
1. Update `quizzes.docx` with your questions
2. Push to GitHub
3. Quizzes post automatically
4. Repeat!

---

## 💡 Pro Tips

- **Update Quizzes:** Edit `quizzes.docx` and push → Quizzes update automatically
- **Manual Post:** Use "Run workflow" button anytime
- **Monitor:** Check Actions tab to see logs
- **Debug:** Read workflow logs for errors
- **Schedule:** Use [crontab.guru](https://crontab.guru) for timing

---

## 🔗 Useful Links

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Cron Schedule](https://crontab.guru)
- [@BotFather](https://t.me/botfather)

---

**Happy automatic quizzing!** 🎉🚀
