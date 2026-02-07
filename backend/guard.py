from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse 
from pydantic import BaseModel
import os
import json
import requests
import uuid 
import re 

# IMPORTACIONES DE BASE DE DATOS
from database import init_db, get_cached_audit, save_audit

# ==========================================
# 🔐 1. CONFIGURACIÓN DE CLAVES
# ==========================================

from dotenv import load_dotenv

# Cargar variables desde .env (si existe)
load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    print("⚠️ [ADVERTENCIA] No se detectaron claves API en el entorno dee GROQ.")

# ==========================================
# 📦 2. IMPORTACIONES MOTORES
# ==========================================
from osint_engine import OSINT_Engine
from pdf_engine import PDFReportGenerator 
from ai_engine import NeuralOrchestrator
from solana_engine import SolanaRPCEngine # <--- NUEVO MOTOR RPC

# --- INICIALIZACIÓN ---
app = FastAPI(title="ChainGuard Cortex", version="6.5 - Solana Validated")
osint_tool = OSINT_Engine()
orchestrator = NeuralOrchestrator()
sol_engine = SolanaRPCEngine() # <--- INSTANCIA RPC

@app.on_event("startup")
def startup_event():
    try:
        init_db()
        print("[SISTEMA] ✅ Conexión a Base de Datos establecida.")
    except Exception as e:
        print(f"[SISTEMA] ⚠️ Alerta: Base de datos no disponible: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELOS ---
class ContractRequest(BaseModel):
    code_snippet: str 
    chain_id: str = "1" 

class InvestigateRequest(BaseModel):
    target: str
    chain_id: str = "1" 

# ==========================================
# 🧠 PROMPTS DE IA
# ==========================================
SYSTEM_PROMPT_EVM = """
Eres un Auditor de Smart Contracts Senior (EVM). Tu salida debe ser ESTRICTAMENTE JSON.
NO escribas texto introductorio. NO escribas conclusiones fuera del JSON.

CRITERIOS:
1. Tokens verificados (AAVE, USDT...) -> SEGURO.
2. Funciones estándar -> SEGURO.
3. PELIGRO: Minting público sin owner, Rug Pulls claros.
4. 📉 ORACLE MANIPULATION (CRÍTICO):
   - ¿El contrato usa `getReserves()`, `slot0` (UniswapV3) o `balanceOf(pair)` para calcular precios o colateral?
   - SI NO usa Chainlink, TWAP o un Oráculo externo -> Veredicto: PELIGRO (Riesgo Flash Loan).
   - Explicación: "Uso de precio spot manipulable mediante Flash Loans."

5. 🔓 CONTROL DE ACCESO:
   - Funciones críticas (`withdraw`, `mint`, `setOwner`) sin `onlyOwner` o modificadores de seguridad -> PELIGRO.

6. 💸 LÓGICA FINANCIERA:
   - Reentrancy, Integer Overflow (pre-0.8.0), Fee-on-transfer tokens rompiendo contabilidad.

Devuelve SOLO este objeto JSON:
{
  "veredicto": "SEGURO" | "PRECAUCIÓN" | "PELIGRO",
  "riesgo": (0-100),
  "tipo_vulnerabilidad": "Resumen corto",
  "ubicacion": "Función/Línea",
  "explicacion": "Análisis detallado en Markdown."
}
"""

SYSTEM_PROMPT_SOLANA = """
Eres un Auditor de Seguridad Senior especializado en SOLANA.
Recibirás código Rust O DATOS DE RPC EN TIEMPO REAL.
Tu trabajo es interpretar esos datos técnicos y dar un veredicto de seguridad.

SI LOS DATOS RPC DICEN "MINT AUTHORITY ACTIVA":
- Veredicto: PELIGRO (Riesgo 90-100)
- Explicación: El creador puede imprimir tokens infinitos y hundir el precio.

SI LOS DATOS RPC DICEN "FREEZE AUTHORITY ACTIVA":
- Veredicto: PELIGRO/PRECAUCIÓN (Riesgo 70-90)
- Explicación: El creador puede congelar fondos de usuarios.

ESTRUCTURA JSON FINAL (MANDATORIA):
{
  "veredicto": "SEGURO" | "PRECAUCIÓN" | "PELIGRO",
  "riesgo": (0-100),
  "tipo_vulnerabilidad": "Nombre técnico",
  "ubicacion": "On-Chain Authority Check",
  "explicacion": "Análisis técnico en Markdown basado en los datos proporcionados."
}
"""

SYSTEM_PROMPT_CASPER = """
Eres un Auditor en CASPER NETWORK (Rust/WASM). Salida ESTRICTAMENTE JSON.
JSON FINAL:
{
  "veredicto": "SEGURO" | "PRECAUCIÓN" | "PELIGRO",
  "riesgo": (0-100),
  "tipo_vulnerabilidad": "Nombre corto",
  "ubicacion": "Función",
  "explicacion": "Resumen técnico."
}
"""

# --- HELPERS ---
def detectar_tipo_entrada(entrada):
    if entrada.startswith("0x") and len(entrada) == 42: return "EVM_ADDRESS"
    if re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", entrada): return "SOL_ADDRESS"
    if re.match(r"^(01[0-9a-fA-F]{64}|02[0-9a-fA-F]{66})$", entrada): return "CASPER_ADDRESS"
    if "#[account]" in entrada or "AnchorSerialize" in entrada: return "SOL_CODE"
    if "casper_contract" in entrada or "runtime::" in entrada: return "CASPER_CODE"
    return "EVM_CODE"

def obtener_codigo_etherscan(direccion, chain_id):
    print(f"[NEXO-EVM] Buscando: {direccion}")
    url = f"https://api.etherscan.io/v2/api?chainid={chain_id}&module=contract&action=getsourcecode&address={direccion}&apikey={ETHERSCAN_API_KEY}"
    try:
        r = requests.get(url, headers={'User-Agent': 'ChainGuard'}, timeout=10)
        d = r.json()
        if d['message'] == 'OK' and d['result']: return d['result'][0]['SourceCode']
        return None
    except: return None

def obtener_codigo_solscan(direccion):
    print(f"[NEXO-SOL] Consultando Solscan: {direccion}")
    url = f"https://pro-api.solscan.io/v1.0/account/verification?address={direccion}"
    try:
        r = requests.get(url, headers={'token': SOLSCAN_API_KEY}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if 'data' in data and 'raw_code' in data['data']: return data['data']['raw_code']
            return None # Si no hay código verificado
        return None
    except: return None

# --- ENDPOINTS ---
@app.get("/")
def home():
    return {"status": "Online", "system": "ChainGuard v6.5"}

# 🛡️ ENDPOINT 1: AUDITORÍA (IA + RPC REAL TIME)
@app.post("/auditar")
def auditar_contrato(request: ContractRequest):
    entrada = request.code_snippet.strip()
    tipo = detectar_tipo_entrada(entrada)
    print(f"[NEXO-ROUTER] Objetivo detectado: {tipo}")

    # CACHÉ CHECK
    if "ADDRESS" in tipo: 
        cached = get_cached_audit(entrada, request.chain_id)
        if cached:
            print(f"[CACHE] ⚡ ¡ENCONTRADO!")
            return cached

    codigo_final = entrada
    origen_datos = "INPUT_DIRECTO"
    prompt_activo = SYSTEM_PROMPT_EVM 
    
    # LÓGICA DE OBTENCIÓN DE DATOS
    if tipo == "EVM_ADDRESS":
        c = obtener_codigo_etherscan(entrada, request.chain_id)
        if c: 
            codigo_final = c
            origen_datos = "Ethereum Mainnet (VERIFICADO)"
        else: raise HTTPException(404, "Código EVM no encontrado.")

    elif tipo == "SOL_ADDRESS":
        prompt_activo = SYSTEM_PROMPT_SOLANA
        origen_datos = "Solana Mainnet (RPC + Code)"
        
        # 1. Intentar obtener código fuente (Solscan)
        c = obtener_codigo_solscan(entrada)
        
        # 2. 🔥 OBTENER ESTADO REAL ON-CHAIN (RPC) 🔥
        # Aquí sucede la magia: Preguntamos a la blockchain si hay peligro
        rpc_data = sol_engine.analizar_token(entrada)
        
        # Construimos el "Contexto" para la IA
        contexto_rpc = ""
        if "error" not in rpc_data:
            contexto_rpc = f"""
            \n=== 🚨 REPORTE DE INTELIGENCIA ON-CHAIN (RPC) ===
            {rpc_data.get('info_tecnica', 'Sin datos técnicos')}
            Riesgos Detectados por RPC: {rpc_data.get('riesgos', [])}
            """
        else:
            contexto_rpc = f"\n[RPC INFO]: {rpc_data['error']}"

        # Unimos todo para dárselo a la IA
        codigo_final = f"{contexto_rpc}\n\n=== CÓDIGO FUENTE (Si disponible) ===\n{c if c else 'Código fuente no público.'}"

    elif tipo == "SOL_CODE":
        prompt_activo = SYSTEM_PROMPT_SOLANA
        origen_datos = "Código Solana/Anchor"
    elif tipo == "CASPER_ADDRESS":
        prompt_activo = SYSTEM_PROMPT_CASPER
        origen_datos = "Casper Network"
        codigo_final = f"Dirección Casper: {entrada}. Pegar código manual."
    elif tipo == "CASPER_CODE":
        prompt_activo = SYSTEM_PROMPT_CASPER
        origen_datos = "Código Casper"

    # HYDRA EXECUTION
    print(f"[NEXO] Enviando a Hydra AI ({origen_datos})...")
    try:
        res = orchestrator.audit_contract(prompt_activo, codigo_final[:30000]) # Aumentamos buffer
        texto_ia = res["content"]
        
        json_final = {}
        
        # PARSER SNIPER V2
        match_codeblock = re.search(r"```json\s*([\s\S]*?)\s*```", texto_ia)
        matches_brackets = re.findall(r"\{[\s\S]*\}", texto_ia)

        if match_codeblock:
            try: json_final = json.loads(match_codeblock.group(1))
            except: pass

        if not json_final and matches_brackets:
            try:
                candidato = max(matches_brackets, key=len)
                if "veredicto" in candidato: json_final = json.loads(candidato)
            except: pass

        if not json_final:
             json_final = {
                 "veredicto": "PRECAUCIÓN", 
                 "riesgo": 50, 
                 "tipo_vulnerabilidad": "Análisis Texto", 
                 "ubicacion": "General",
                 "explicacion": texto_ia
             }
        
        if "explicacion" not in json_final or len(json_final["explicacion"]) < 10:
             json_final["explicacion"] = texto_ia.replace(json.dumps(json_final), "").strip() or "Ver PDF."

        json_final['origen_codigo'] = origen_datos
        json_final['ai_provider'] = res["provider"]

        # GUARDAR EN CACHÉ
        if "ADDRESS" in tipo and json_final.get("veredicto"):
            save_audit(entrada, request.chain_id, json_final)

        return json_final

    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(500, f"Error Hydra: {e}")

# 🕵️‍♂️ ENDPOINT 2: INVESTIGACIÓN (OSINT HÍBRIDO)
@app.post("/investigar")
def investigar_objetivo(request: InvestigateRequest):
    target = request.target.strip()
    chain_id = request.chain_id
    print(f"[NEXO-OSINT] Investigando: {target}")

    resultado = {}
    tipo_detectado = "DESCONOCIDO"

    # A. INTENTO 1: ¿Es una dirección (0x...)?
    if target.startswith("0x") and len(target) == 42:
        print("[OSINT] Probando si es un Token/Contrato...")
        datos_token = osint_tool.analizar_token_goplus(target, chain_id)
        
        if "error" not in datos_token:
            tipo_detectado = "SMART_CONTRACT_ASSET"
            resultado = datos_token
            # Recursividad creador
            creador = datos_token.get("creador_address")
            if creador:
                datos_creador = osint_tool.investigar_usuario(creador)
                resultado["huella_digital_web2"] = datos_creador.get("huella_digital_web2", [])
                resultado["identidad_web3"] = datos_creador.get("identidad_web3", {})
        else:
            print("[OSINT] Fallo Token -> Modo Wallet.")
            tipo_detectado = "DIGITAL_IDENTITY"
            resultado = osint_tool.investigar_usuario(target)

    # B. DOMINIO WEB
    elif "." in target and not target.endswith(".eth") and not target.endswith(".sol"):
        tipo_detectado = "DOMAIN_NAME"
        resultado = osint_tool.analizar_dominio(target)

    # C. USUARIO / ENS
    else:
        tipo_detectado = "DIGITAL_IDENTITY"
        resultado = osint_tool.investigar_usuario(target)

    return {
        "status": "success",
        "tipo": tipo_detectado,
        "datos": resultado
    }

# 📄 ENDPOINT 3: REPORTE PDF
@app.post("/reporte")
def reporte_pdf(request: dict): 
    try:
        filename = f"reporte_{uuid.uuid4().hex[:8]}.pdf"
        filepath = os.path.join(os.getcwd(), filename)
        PDFReportGenerator(filepath).generar_informe_auditoria(request) 
        return FileResponse(filepath, media_type='application/pdf', filename="ChainCortex_Reporte.pdf")
    except Exception as e:
        print(f"[ERROR PDF] {e}")
        raise HTTPException(500, "Error PDF")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)