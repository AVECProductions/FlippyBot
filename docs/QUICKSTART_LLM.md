# 🚀 LLM AI Deal Analyzer - Quick Start Guide

Get your AI-powered deal analysis up and running in 5 minutes!

---

## Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `google-adk` - Google Agent Development Kit
- `httpx` - Async HTTP client for images
- `google-generativeai` - Gemini API

---

## Step 2: Get Your API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy your API key

---

## Step 3: Configure Environment

Add this line to `backend/.env`:

```bash
GEMINI_API_KEY=your_actual_api_key_here
```

**💡 Tip**: You can also use `GOOGLE_API_KEY` instead.

---

## Step 4: Test the Setup

Run the test script to verify everything works:

```bash
cd backend
python test_llm_analysis.py
```

You should see:
```
✅ API key found
✅ Found listings with images
🤖 Analyzing with LLM...
✅ TEST COMPLETED SUCCESSFULLY
```

---

## Step 5: Use in the UI

1. Start your backend: `python manage.py runserver`
2. Start your frontend: `npm run dev`
3. Navigate to **Scanner Control**
4. Click on any scan batch
5. **Right-click a listing** → Select "🤖 Analyze with AI"
6. View the AI analysis in the modal!

---

## What You Get

The AI will analyze:
- ✅ Brand and model identification
- ✅ Condition assessment from images
- ✅ Market value estimation
- ✅ Deal quality (NOTIFY or IGNORE)
- ✅ Detailed pros and cons
- ✅ Red flags and considerations
- ✅ Automatic email notifications for good deals

---

## Troubleshooting

### "GEMINI_API_KEY not found"
→ Check your `backend/.env` file. Make sure the key is there and there are no extra spaces.

### "No listings found in database"
→ Run a scanner first to create some listings:
```bash
python manage.py run_scanner
```

### "Analysis failed"
→ Check the logs in `backend/logs/` for detailed error messages.

---

## Next Steps

- ✅ Read the full setup guide: `docs/LLM_SETUP_GUIDE.md`
- ✅ Review implementation details: `docs/LLM_IMPLEMENTATION_SUMMARY.md`
- ✅ Check the master plan: `docs/LLM_SKI_ANALYZER_PLAN.md`

---

## Cost Information

**Per Analysis**: ~$0.0035 (less than half a penny!)

**Monthly Estimates**:
- Manual testing (20/day): ~$2/month
- Light usage (100/day): ~$10/month
- Heavy usage (500/day): ~$53/month

Start with manual testing to keep costs low while you evaluate the system.

---

## Support

Questions? Check the troubleshooting section in `docs/LLM_SETUP_GUIDE.md`.

**Status**: ✅ Ready to use! The UI layers are already built, just add your API key and go.

---

**That's it! You're ready to start analyzing deals with AI.** 🎉
