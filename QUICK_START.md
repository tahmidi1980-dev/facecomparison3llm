# ⚡ QUICK START - Deploy in 10 Minutes

## 🎯 **FASTEST WAY TO DEPLOY**

### **Step 1: Upload to GitHub (2 minutes)**

```bash
# 1. Create new repo on GitHub.com
#    - Name: face-comparison-streamlit
#    - Public repository

# 2. Clone and upload code
git clone https://github.com/YOUR_USERNAME/face-comparison-streamlit.git
cd face-comparison-streamlit

# 3. Copy all files from streamlit-version folder here
# Then:
git add .
git commit -m "Initial commit"
git push
```

### **Step 2: Deploy to Streamlit (5 minutes)**

1. Go to: **https://share.streamlit.io/**
2. Sign in with GitHub
3. Click **"New app"**
4. Fill in:
   - Repository: `YOUR_USERNAME/face-comparison-streamlit`
   - Branch: `main`
   - Main file: `streamlit_app.py`

5. Click **"Advanced settings"**
6. Add **Secrets**:
   ```
   QWEN_API_KEY = "sk-or-v1-your-qwen-key"
   CHATGPT_API_KEY = "sk-or-v1-your-chatgpt-key"
   GEMINI_API_KEY = "sk-or-v1-your-gemini-key"
   ```

7. Click **"Deploy!"**

### **Step 3: Wait (3 minutes)**

App will be live at:
```
https://YOUR_USERNAME-face-comparison-streamlit-main-xxxx.streamlit.app
```

## ✅ **THAT'S IT!**

Your app is now:
- ✅ Live on the internet
- ✅ HTTPS enabled
- ✅ Free hosting
- ✅ Auto-deploys on git push

---

## 🔑 **GET API KEYS**

1. Go to: https://openrouter.ai/
2. Sign up
3. Go to "Keys" section
4. Create new key
5. Copy and paste to Streamlit Secrets

---

## 🧪 **TEST LOCALLY FIRST** (Optional)

```bash
# Install dependencies
pip install -r requirements.txt

# Add API keys to .env
cp .env.example .env
nano .env

# Run locally
streamlit run streamlit_app.py
```

Visit: http://localhost:8501

---

## 🆘 **NEED HELP?**

- 📖 Full Guide: See `README_STREAMLIT.md`
- 🐛 Issues: Check Streamlit Cloud logs
- 💬 Ask: https://discuss.streamlit.io/

---

## 🎉 **YOU'RE DONE!**

Time to deploy: **~10 minutes**

Share your app and start comparing faces! 🎭
