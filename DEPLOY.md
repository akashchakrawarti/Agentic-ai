# Deploying to Streamlit Community Cloud (free)

1. Create a GitHub account and a new **private** repo (e.g. `skilled-sapiens-agent`).
2. Upload everything in this folder to the repo (do NOT upload `.env`).
3. Go to https://share.streamlit.io -> sign in with GitHub -> **Create app**.
   - Repository: your repo
   - Branch: main
   - Main file path: `app.py`
4. Click **Advanced settings -> Secrets** and paste:

       GROQ_API_KEY = "gsk_your_real_key"
       TAVILY_API_KEY = "tvly_your_real_key"

5. Click **Deploy**. In ~2-3 minutes you get a URL like
   `https://your-app-name.streamlit.app` that works any time.

## Keep it private (recommended)
Anyone with the link can use it and spend your free Groq/Tavily quota.
In the app's **Settings -> Sharing**, choose "Only specific people can view"
and add your email(s).

## Notes
- Free apps go to sleep after ~12 hours of no visitors; open the URL and
  click "Wake up" (takes ~30 seconds).
- `rag.py` is not used by the app, so the heavy ML packages are not installed
  (see `requirements-rag.txt` if you want to run `test_phase4.py` locally).
