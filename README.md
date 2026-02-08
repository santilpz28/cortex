🛡️ ChainCortex (Beta)
Advanced Web3 Security Scanner & OSINT Intelligence
(Insertar captura de pantalla de la UI aquí)

ChainCortex es una herramienta de ciberseguridad Web3 diseñada como "Primera Línea de Defensa" para inversores retail y auditores. No busca competir con auditorías profundas (como Zellic o Certik), sino ofrecer un análisis rápido (5-10s) para detectar Red Flags, vulnerabilidades críticas y riesgos de centralización antes de interactuar con un contrato.

👉 Demo en vivo: https://chain-cortex.com

🚀 Key Features
1. 🧠 Hydra AI Orchestrator
Sistema de orquestación de LLMs resiliente.

Failover Automático: Si Groq (Llama-3-70b) alcanza su límite, el sistema cambia automáticamente a Google Gemini en milisegundos.

Cero Downtime: El usuario nunca recibe un error 429 Too Many Requests.

2. 🦀 Solana RPC Tactical Engine
A diferencia de los analizadores tradicionales que intentan leer bytecode de Solana (y fallan), ChainCortex interroga directamente a la Mainnet (RPC) para validar hechos matemáticos:

Mint Authority Check: ¿Puede el creador imprimir tokens infinitos?

Freeze Authority Check: ¿Pueden congelar tu wallet?

Supply Analysis: Verificación de datos on-chain reales.

3. 🛡️ EVM Vulnerability Scanner
Descarga y analiza código verificado de Etherscan/BscScan buscando patrones de ataque clásicos:

Reentrancy Attacks.

Oracle Manipulation (Flash Loans).

Unchecked External Calls.

Honeypot Logic.

4. 🕵️‍♂️ Hybrid OSINT Module
La seguridad no es solo código, es identidad.

Project vs. Wallet: Detecta si la dirección pertenece a un usuario o a un contrato.

Digital Footprint: Busca rastros del creador en GitHub, Twitter, Dune Analytics y bases de datos de hacks (Rekt.news).

5. ⚡ Smart Caching (PostgreSQL)
Implementación de arquitectura eficiente:

Cada auditoría se guarda en base de datos.

Si un usuario consulta un contrato ya auditado < 24h, la respuesta es instantánea (0ms) y coste cero de API.

🛠️ Tech Stack
Backend: Python (FastAPI).

AI Engine: Groq (Llama-3), Google Gemini.

Blockchain Data: Etherscan API, Solana RPC, Solscan.

Database: PostgreSQL (Production) / SQLite (Dev).

Containerization: Docker & Docker Compose.

Frontend: HTML5/JS (Cyberpunk UI).

🔧 Installation & Local Setup
Si quieres correr tu propia instancia de ChainCortex:

Prerrequisitos
Docker & Docker Compose

API Keys (Groq, Gemini, Etherscan, Solscan)

1. Clonar el Repositorio
Bash
git clone https://github.com/TU_USUARIO/ChainCortex.git
cd ChainCortex
2. Configurar Variables de Entorno
Crea un archivo .env en la raíz:

Bash
cp .env.example .env
Y rellena tus claves:

Fragmento de código
GROQ_API_KEY="gsk_..."
GEMINI_API_KEY="AIza..."
ETHERSCAN_API_KEY="YourKey"
SOLSCAN_API_KEY="YourKey"
DATABASE_URL="postgresql://user:pass@db:5432/chainguard"
3. Desplegar con Docker
Bash
docker-compose up -d --build
El backend estará disponible en http://localhost:8000 y la UI en http://localhost:8080.

📖 Usage Examples
Auditoría de Contrato (API)
HTTP
POST /auditar
Content-Type: application/json

{
  "code_snippet": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
  "chain_id": "1"
}
Investigación OSINT
HTTP
POST /investigar
Content-Type: application/json

{
  "target": "vitalik.eth"
}
🗺️ Roadmap
[x] EVM Static Analysis

[x] Solana RPC Integration

[x] OSINT Module (Web2 + Web3)

[x] PDF Report Generation

[ ] Support for Tron & Base

[ ] Telegram Bot Integration

🤝 Contributing
Las contribuciones son bienvenidas. Por favor, abre un Issue para discutir cambios mayores antes de enviar un Pull Request.

📄 License
Este proyecto está bajo la licencia MIT. Eres libre de usarlo, modificarlo y distribuirlo.

🎓 Acknowledgments
Proyecto desarrollado como parte del Trabajo Final de Grado (TFG) y optimizado con conocimientos de ciberseguridad Web3 impartidos por @0xjmaria.

Built with 💻 and ☕ by Santiago López.

💡 Tip Pro:
No olvides crear un archivo llamado .env.example en tu repo que tenga solo los nombres de las variables VACÍAS, para que la gente sepa qué poner sin ver tus claves reales:

Archivo .env.example:

Fragmento de código
GROQ_API_KEY=""
GEMINI_API_KEY=""
ETHERSCAN_API_KEY=""
SOLSCAN_API_KEY=""
DATABASE_URL="sqlite:///./local.db"
