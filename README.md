Markdown
# 🛡️ ChainCortex (Beta)
### Advanced Web3 Security Scanner & OSINT Intelligence

![Build Status](https://img.shields.io/badge/build-passing-brightgreen?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95-009688?style=flat-square&logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

> **"The First Line of Defense for Retail Investors."**

---

## 🖼️ Dashboard Preview

![ChainCortex Dashboard]
*(Reemplaza esta línea con una captura real de tu interfaz Cyberpunk)*

---

## 🚀 About The Project

**ChainCortex** no es otra herramienta de análisis estático. Es un ecosistema de ciberseguridad diseñado para **democratizar la auditoría de Smart Contracts**.

A diferencia de las firmas de auditoría tradicionales que tardan semanas y cuestan miles de dólares, ChainCortex ofrece un análisis de **reconocimiento táctico en segundos**. Combina la potencia de **LLMs (Llama-3 & Gemini)** con verificación de datos **On-Chain en tiempo real (RPC)** e inteligencia de fuentes abiertas (**OSINT**).

👉 **Live Demo:** [https://chain-cortex.com](https://chain-cortex.com)

---

## 🔥 Key Features

### 🧠 1. Hydra AI Orchestrator
Un sistema de IA resiliente y redundante.
* **Failover Automático:** Si el proveedor principal (Groq) falla o alcanza el límite de rate, el sistema cambia instantáneamente a Google Gemini.
* **Zero Downtime:** Arquitectura diseñada para mantener el servicio activo incluso bajo estrés de API.

### 🦀 2. Solana RPC Tactical Engine
La mayoría de scanners fallan en Solana porque intentan "leer" el bytecode. ChainCortex consulta directamente a la **Mainnet**:
* **Mint Authority Check:** Detecta si el creador puede imprimir tokens infinitos.
* **Freeze Authority Check:** Alerta si la wallet del desarrollador puede congelar fondos de usuarios.
* **Supply Validation:** Datos matemáticos reales vs declarados.

### 🛡️ 3. EVM Vulnerability Scanner
Para Ethereum y compatibles (BSC, Polygon...), analizamos el código fuente verificado en busca de:
* Reentrancy Attacks.
* Oracle Manipulation (Flash Loan Risks).
* Unchecked External Calls.
* Honeypot Logic & Ownership Renouncement.

### 🕵️‍♂️ 4. Hybrid OSINT Module
Rastreamos la huella digital más allá del código:
* **Identidad vs Proyecto:** Diferenciación automática entre Wallets personales y Contratos.
* **Digital Footprint:** Búsqueda automatizada en GitHub, Twitter, Dune Analytics y bases de datos de hacks (Rekt.news).

---

## 🛠️ Tech Stack

| Componente | Tecnología | Descripción |
| :--- | :--- | :--- |
| **Backend** | ![Python](https://img.shields.io/badge/-Python-black?logo=python) **FastAPI** | API de alto rendimiento asíncrono. |
| **AI Engine** | ![Groq](https://img.shields.io/badge/-Groq-orange) ![Google](https://img.shields.io/badge/-Gemini-blue) | Modelos Llama-3-70b y Gemini 1.5 Flash. |
| **Database** | ![Postgres](https://img.shields.io/badge/-PostgreSQL-336791?logo=postgresql) | Caché inteligente para reducir costes de API. |
| **Infra** | ![Docker](https://img.shields.io/badge/-Docker-2496ED?logo=docker) | Contenerización completa con Docker Compose. |
| **Blockchain** | **RPC / Etherscan** | Conexión directa a nodos para validación. |

---

## 🔧 Installation (Local)

Si quieres desplegar tu propia instancia de ChainCortex:

### 1. Clonar Repositorio
```bash
git clone [https://github.com/TU_USUARIO/ChainCortex.git](https://github.com/TU_USUARIO/ChainCortex.git)
cd ChainCortex
2. Configurar Variables de Entorno
Crea un archivo .env en la raíz (puedes copiar .env.example):

Bash
GROQ_API_KEY="gsk_..."
GEMINI_API_KEY="AIza..."
ETHERSCAN_API_KEY="YourKey"
SOLSCAN_API_KEY="YourKey"
DATABASE_URL="sqlite:///./local_backup.db" # Para desarrollo local
3. Desplegar con Docker
Bash
docker-compose up -d --build
Frontend UI: http://localhost:8080

Backend API: http://localhost:8000/docs

📖 API Usage
ChainCortex expone una API RESTful documentada en Swagger.

Ejemplo: Auditar Contrato
HTTP
POST /auditar
Content-Type: application/json

{
  "code_snippet": "0xdAC17F958D2ee523a2206206994597C13D831ec7", // USDT Address
  "chain_id": "1"
}
Ejemplo: Respuesta (JSON)
JSON
{
  "veredicto": "PRECAUCIÓN",
  "riesgo": 45,
  "tipo_vulnerabilidad": "Centralización",
  "explicacion": "El contrato tiene funciones de Pausa y Blacklist controladas por el owner..."
}
🗺️ Roadmap
[x] EVM Static Analysis

[x] Solana RPC Integration

[x] OSINT Module (Web2 + Web3)

[x] Producción: Despliegue en VPS con SSL/HTTPS

[ ] Support for Tron & Base Chains

[ ] Telegram Bot Integration for alerts

🤝 Contributing
Las contribuciones son bienvenidas. Si tienes ideas para mejorar el motor de detección o añadir nuevas redes:

Haz un Fork del proyecto.

Crea una rama (git checkout -b feature/AmazingFeature).

Haz Commit (git commit -m 'Add some AmazingFeature').

Haz Push (git push origin feature/AmazingFeature).

Abre un Pull Request.

🎓 Acknowledgments
Proyecto desarrollado como parte del Trabajo Final de Grado (TFG). Especial agradecimiento a @0xjmaria por la mentoría en seguridad Web3 y Smart Contract Auditing.

Built with 💻, ☕ and 🛡️ by Santiago López.
