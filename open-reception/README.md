# Luna Open Reception MVP

Human identity and accountability remain authoritative. AI agents are recommendation and drafting systems, not legal persons, employers, or contract parties.

## Flow

1. `POST /auth/register`
2. `POST /auth/login`
3. `PUT /passport/human`
4. `POST /steward-human/applications`
5. Human administrator review
6. `POST /matching/recommendations`
7. Separate Human approval before any future delegation

The MVP never executes payments, contracts, or external messages. Matching returns explanations and candidates only. Junior agents always require supervision. A global kill switch blocks matching immediately.

## Local validation

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

For the complete stack, copy `.env.example` to `.env`, replace every placeholder, and run:

```bash
docker compose config
docker compose up --build
```
