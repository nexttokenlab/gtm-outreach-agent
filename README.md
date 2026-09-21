# GTM Outreach Agent

A Streamlit app that orchestrates four specialist agents using GPT-5 and Exa: Company Finder → Contact Finder → Researcher → Email Writer.

## Run locally

Python 3.10+ recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run advanced_ai_agents/multi_agent_apps/ai_email_gtm_outreach_agent/ai_email_gtm_outreach_agent.py
```

Enter `OPENAI_API_KEY` and `EXA_API_KEY` in the sidebar, or set them in your shell. `.env` files are not loaded automatically. Never commit secrets.

Describe your target companies and offering, select 1–10 companies and a Professional, Casual, Cold, or Consultative email style, then select **Start Outreach**. Review the contacts, research sources, and email drafts. Copy emails using the code block copy control, or download Markdown, JSON, or individual text drafts.

## Behavior

- Four separate specialist prompts, typed handoffs, and a deterministic orchestration loop; no agent framework required.
- GPT-5 is the default. The sidebar accepts another model with Responses API and structured output support if GPT-5 is unavailable in your account.
- Exa searches company information, decision makers, official website pages, and Reddit.
- Up to 2–3 contacts and 2–4 insights per company. Returns fewer when evidence is insufficient rather than inventing results.
- Inferred business emails are opt-in and labeled. Published emails are checked against retrieved source text. Neither status guarantees deliverability or current ownership. Sources and roles require human review.
- Strict Pydantic structured outputs avoid free-form JSON parsing. Unknown citations are dropped.
- Timeouts and bounded retries handle transient errors. **Resume unfinished stages** preserves completed stages and individual drafts in the current session. Starting a new run replaces old results.
- Drafts only: the app does not send email.

## Privacy and operation

Keys stay in process/session memory, are not written to disk, and are excluded from exports. OpenAI requests use `store=False`. Targeting and search queries go to Exa; your brief and retrieved evidence go to OpenAI. Provider retention policies still apply. Results are session-local, not a durable database; reconnecting/restarting can lose them. Download anything you want to keep.

Run locally for personal use. A hosted deployment needs appropriate authentication and TLS. API calls incur usage charges. For larger runs, allow several minutes.

## Troubleshooting

- **Authentication/model errors:** check sidebar keys, account access, and model name.
- **Rate limits:** wait and resume, or start a smaller run.
- **Network/timeouts:** check connectivity, then resume; completed work is retained.
- **No companies/contacts/Reddit insights:** broaden targeting; some information is not publicly indexed.

## Test without API keys

```bash
pip install pytest
pytest -q
```

Tests use mocked providers and Streamlit AppTest. Live provider execution requires your keys.

## API references

- [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [GPT-5](https://developers.openai.com/api/docs/models/gpt-5)
- [Exa search API](https://exa.ai/docs/reference/search)
