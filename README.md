<div align="center">

# 🛡️ ChainGuard.ai — Web3 Risk Intelligence Platform

**Production-grade microservices platform for smart contract risk analysis and crypto scam detection.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-FF5722?style=for-the-badge&logo=google-chrome&logoColor=white)](https://santilpz28.github.io/chainguard-pages/)
[![Backend Health](https://img.shields.io/badge/API-Online-success?style=for-the-badge&logo=fastapi&logoColor=white)](https://chainguard.santilpz28.com/)
[![Tests](https://img.shields.io/badge/Tests-34%2F34-success?style=for-the-badge&logo=pytest&logoColor=white)](#testing)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

**Detect. Explain. Protect.**
*Pega una dirección o nombre de token. Te diremos si es seguro.*

[English](#english) · [Español](#español) · [日本語](#日本語) — ver [CONTRIBUTING.md](CONTRIBUTING.md) para más idiomas

</div>

---

## 🎯 What is ChainGuard.ai?

ChainGuard is a **multi-chain risk intelligence platform** that combines on-chain signals (Etherscan, Solscan), repository metadata, and OSINT sources (VirusTotal, Shodan, Whois) into unified risk scores for Web3 domains, contracts, and addresses.

**Why it matters:** Investors lose **$60B+ annually** to crypto scams (LUNA/UST collapse, FTX, Badger DAO, Cream Finance). ChainGuard helps retail users and DeFi teams **identify red flags before they invest** — liquidity not locked, contract not verified, owner privileges enabled, owner wallet flagged, or contract matched against known exploit patterns.

### 🏆 Key differentiators

- **186-entry crypto dictionary** across 5 chains (ETH 123 · SOL 24 · BSC 10 · ARB 18 · POLY 11) with **9 documented historical exploits** (FTT, LUNA, UST, CEL, BADGER, CREAM, PICKLE, COVER, MNGO)
- **Didactic mode** — each vulnerable protocol opens a modal with the loss in USD, exploit type, and security lessons (e.g. "FTX: $8B misappropriation, always verify proof-of-reserves")
- **Defense-in-depth** — 3-layer whitelist (JS client → PHP proxy → Python backend), same regex `^[a-zA-Z0-9\s._\-]{1,64}$` enforced at every layer
- **34/34 security tests passing** (15 explicit injection attacks: SQLi, XSS, SSTI, Log4Shell, command injection, path traversal, prototype pollution, null bytes)
- **Hydra AI orchestrator** — multi-model failover (Groq + Cerebras + Gemini) with <200ms fallback
- **Web3 wallet auth** — EIP-712 typed-data signatures, no third-party custodians

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  PHP Proxies    │    │  Backend (FastAPI)│  │  External APIs  │
│   (HTML/JS)     │────│  (Apache)       │────│  (Python 3.10)   │───│  Etherscan V2   │
│                 │    │                 │    │                 │    │  Solscan v1.0   │
│  - datalist     │    │  - audit_proxy  │    │  - guard.py     │    │  CoinGecko      │
│  - chips        │    │  - osint_proxy  │    │  - ai_engine    │    │  VirusTotal     │
│  - didactic UI  │    │  - dict_proxy   │    │  - osint_engine │    │  Shodan         │
│  - wallet EIP712│    │  - wallet_proxy │    │  - dict_engine  │    │  Hydra LLMs     │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                         │
                              │ 3-layer whitelist       │ TTL cache + rate-limit
                              ▼                         ▼
                       ┌──────────────────────────────────────┐
                       │  PostgreSQL  +  Prometheus  +  Redis │
                       └──────────────────────────────────────┘
```

### Services

| Service | Tech | Purpose |
|---|---|---|
| `frontend/` | HTML, Tailwind, vanilla JS | Single-page UI, autocompletado, didáctica |
| `backend/guard.py` | FastAPI | Public API (audit, investigate, wallet, dict) |
| `backend/ai_engine.py` | Python | Hydra multi-model orchestrator (Groq / Cerebras / Gemini fallback) |
| `backend/osint_engine.py` | Python | VirusTotal + Shodan + Whois + Etherscan V2 + Solscan |
| `backend/dict_engine.py` | Python | Crypto dictionary search, ranking, didactic mode |
| `backend/solana_engine.py` | Python | Solana program analysis (SPL tokens, anchor) |
| `backend/pdf_engine.py` | Python | Audit report generation (PDF) |
| `frontend/*.php` | Apache/PHP | Reverse proxies with 2nd-layer validation |

---

## ✨ Features

### 🔍 Intelligent OSINT Dictionary v1.0

```bash
GET /dict/suggest?q=eth&limit=8
GET /dict/lookup?chain=ETH&address=0xdAC17F958D2ee523a2a206206994597C13D831ec7
GET /dict/stats
```

**Sample output:**
```json
{
  "results": [
    {
      "symbol": "USDT",
      "name": "Tether USD",
      "chain": "ETH",
      "address": "0xdAC17F958D2ee523a2a206206994597C13D831ec7",
      "category": "stablecoin",
      "vulnerable": false,
      "_score": 1.097
    },
    {
      "symbol": "FTT",
      "name": "FTX Token",
      "chain": "ETH",
      "address": "0x50D1c9771902476076eCfc8B2A83Ad6b9355a4c9",
      "category": "exchange",
      "vulnerable": true,
      "_score": 1.05,
      "didactic": {
        "title": "El colapso de FTX (noviembre 2022)",
        "loss_usd": 8000000000,
        "exploit_type": "Misappropriation of customer funds",
        "summary": "Sam Bankman-Fried...",
        "lesson": "An exchange without auditable proof-of-reserves...",
        "references": ["https://www.rekt.news/ftx-...", "https://www.justice.gov/..."]
      }
    }
  ]
}
```

**Ranking formula:**
```python
score = base_score + market_cap_bonus
market_cap_bonus = 0.1 * (1 - rank/100)  # rank 1 = +0.10, rank 100 = +0.00
```

### 🛡️ Audit Smart Contracts (EVM, Solana, Casper)

```bash
POST /auditar
{
  "chain_id": "ETH",
  "code_snippet": "pragma solidity ^0.8.0; contract Vault { ... }"
}
```

Returns vulnerability report with severity (Critical / High / Medium / Low / Informational), CWE mapping, and remediation suggestions.

### 🔐 EIP-712 Wallet Auth (no third-party)

```javascript
const typedData = {
  domain: { name: "ChainGuard.ai", version: "1", chainId: 1 },
  types: { Authentication: [{ name: "address", type: "address" }, { name: "statement", type: "string" }, { name: "timestamp", type: "uint256" }] },
  message: { address: userAddress, statement: "Sign in to ChainGuard.ai", timestamp: Math.floor(Date.now()/1000) }
};
const signature = await signer.signTypedData(typedData.domain, typedData.types, typedData.message);
```

Backend verifies the signature, ensures timestamp is within 5 minutes (anti-replay), and returns a session token.

### 🤖 Hydra AI Orchestrator (multi-model)

```python
# backend/ai_engine.py
async def analyze_smart_contract(code: str) -> dict:
    return await hydra.complete(
        prompt=code,
        models=[GROQ_LLAMA3_70B, CEREBRAS_LLAMA3_70B, GEMINI_FLASH],
        max_latency_ms=200,
        fallback_strategy="fastest_first"
    )
```

If Groq returns in 80ms, we never call Cerebras. If it fails, automatic fallback to the next model. **p99 < 200ms.**

---

## 🧪 Testing

```bash
# Run the 34-test security suite
docker cp backend/tests/test_dict_security.py chainguard_cortex:/tmp/
docker exec chainguard_cortex python /tmp/test_dict_security.py
```

```
========================================
PASS: 34 | FAIL: 0
========================================
🎯 TODOS LOS TESTS PASADOS
```

**Test coverage includes:**
- 15 injection attack vectors (SQLi, XSS, SSTI, Log4Shell, command injection, path traversal, prototype pollution, null bytes)
- 9 vulnerable entries verification
- Multi-chain address validation (EVM + Solana)
- Whitelist regex at 3 layers
- Hydrate autocompletion with debounce

---

## 🚀 Quickstart (local dev)

### Prerequisites
- Docker + Docker Compose
- 4GB RAM minimum
- API keys (free tier is fine): Etherscan, Solscan, CoinGecko, Groq

### Installation

```bash
git clone https://github.com/santilpz28/cortex.git
cd cortex
cp backend/.env.example backend/.env
# Edit .env with your API keys
docker compose up -d
```

### Verify

```bash
curl http://localhost:8000/
# {"status":"ok","service":"chainguard-cortex","version":"0.5.0"}

curl "http://localhost:8000/dict/suggest?q=eth&limit=3"
# Returns top 3 ETH entries with market cap boost

curl -X POST http://localhost:8000/wallet/verify \
  -H "Content-Type: application/json" \
  -d '{"address":"0x...","chain_id":"ETH","signature":"0x...","typed_data":{...}}'
```

### Open the UI

Visit `http://localhost:8080` and start typing a token name. Autocompletion, didactic mode, and wallet auth are all wired.

---

## 🛣️ Roadmap

### Done (v0.5)
- [x] 186-entry crypto dictionary (62 added in v0.5 via CoinGecko)
- [x] Market cap ranking with 1h cache
- [x] 9 didactic lessons for vulnerable protocols
- [x] 3-layer defense (34/34 tests)
- [x] EIP-712 wallet auth

### Next (v0.6)
- [ ] Retail refactor: hero "Pega una dirección, te diremos si es seguro"
- [ ] Scam check endpoint (liquidity locked, owner renounced, contract verified)
- [ ] Deployer OSINT (other contracts by same wallet)
- [ ] Watchlist (alerts on liquidity drops >20%)

### Future (v1.0)
- [ ] Public API tier (free + Pro)
- [ ] Telegram notifications
- [ ] AI auto-extension of dictionary (proposals to human reviewer)
- [ ] Bug bounty on our own audit platform (eat your own dog food)

---

## 📊 Tech stack

| Layer | Tech |
|---|---|
| Frontend | HTML5, Tailwind CSS, vanilla JS, Ethers.js |
| Backend | Python 3.10, FastAPI, Pydantic 2.0, httpx, asyncio |
| Database | PostgreSQL 15, Redis 7 |
| AI | Groq (Llama 3.1 70B), Cerebras, Gemini Flash |
| External APIs | Etherscan V2, Solscan, CoinGecko, VirusTotal, Shodan, Whois |
| Infra | Docker Compose, Prometheus, Grafana, Apache 2.4 |
| Security | 3-layer whitelist, EIP-712, rate-limit, TTL cache, SSRF guard |
| Testing | pytest, custom 34-test security suite |

---

## 🤝 Contributing

This is a personal portfolio project, but pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📜 License

MIT © 2026 Chain-Cortex. See [LICENSE](LICENSE).

## 📫 Contact

**Santiago López Castaño**
- GitHub: [@santilpz28](https://github.com/santilpz28)
- LinkedIn: [santiagolopez-cyber](https://www.linkedin.com/in/santiagolopez-cyber/)
- Email: santi.lpz28@gmail.com
- Portfolio: [santilpz28.github.io/chainguard-pages](https://santilpz28.github.io/chainguard-pages/)

---

<div align="center">

**Built with discipline of an athlete. Documented with rigor of a pentester. Shipped with care of a maker.**

⚡ *"Auditing the future, one contract at a time."* ⚡

</div>
