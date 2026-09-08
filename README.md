# Adaptive Learning Studio

```
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
cd web && npm install && npm run dev
python -m pytest
```

Demo runs without an API key; set AI_API_KEY/AI_BASE_URL/AI_MODEL to enable the remote LLM.

MIT License.
