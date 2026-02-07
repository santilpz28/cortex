import os
import time
import re
from abc import ABC, abstractmethod
from groq import Groq
from google import genai
from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras

# Cargamos variables de entorno
load_dotenv()

# --- CLAVES ---
KEY_GROQ_1 = os.getenv("GROQ_API_KEY", "")
KEY_GROQ_2 = os.getenv("GROQ_API_KEY_SECONDARY", "") 
KEY_GEMINI = os.getenv("GEMINI_API_KEY", "")
KEY_GEMINI_2 = os.getenv("GEMINI_API_KEY_SECONDARY", "")
KEY_CEREBRAS = os.getenv("CEREBRAS_API_KEY", "")
SOLANA_API_KEY = os.getenv("SOLANA_API_KEY", "")

# --- INTERFAZ BASE ---
class AIProvider(ABC):
    @abstractmethod
    def analyze(self, system_prompt: str, user_content: str) -> str:
        pass

# --- PROVEEDOR 1: GROQ (Llama 3 - 70B) ---
class GroqProvider(AIProvider):
    def __init__(self, api_key, model="llama-3.3-70b-versatile", name="Groq Primary"):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.name = name

    def analyze(self, system_prompt: str, user_content: str) -> str:
        completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            model=self.model,
            temperature=0, 
        )
        return completion.choices[0].message.content

# --- PROVEEDOR 2: CEREBRAS (8B - Backup Rápido) ---
class CerebrasProvider(AIProvider):
    def __init__(self, api_key, model="llama3.1-8b", name="Cerebras Fast"):
        self.client = Cerebras(api_key=api_key)
        self.model = model
        self.name = name

    def analyze(self, system_prompt: str, user_content: str) -> str:
        completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            model=self.model,
            temperature=0, 
        )
        return completion.choices[0].message.content

# --- PROVEEDOR 3: GOOGLE GEMINI (Modelo 2.0 Flash) ---
class GeminiProvider(AIProvider):
    def __init__(self, api_key, name="Google Gemini"):
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash-exp" 
        self.name = name

    def analyze(self, system_prompt: str, user_content: str) -> str:
        # Concatenamos prompts porque la API de Google es distinta
        full_prompt = f"{system_prompt}\n\nANALIZA ESTO:\n{user_content}"
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=full_prompt
        )
        return response.text

# --- EL ORQUESTADOR (HYDRA) ---
class NeuralOrchestrator:
    def __init__(self):
        self.brains = []
        
        # --- ORDEN DE BATALLA ESTRATÉGICO ---
        
        # 1. Google Gemini (Primera línea: Contexto alto y buena disponibilidad)
        if KEY_GEMINI and "AIza" in KEY_GEMINI:
            self.brains.append(GeminiProvider(KEY_GEMINI, "Google Gemini"))

        # 2. Google Gemini Secundario (Segunda línea: Contexto alto y buena disponibilidad)
        if KEY_GEMINI_2 and "AIza" in KEY_GEMINI_2:
            self.brains.append(GeminiProvider(KEY_GEMINI, "Google Gemini"))

        # 2. Groq Principal (Calidad 70B)
        if KEY_GROQ_1 and "gsk_" in KEY_GROQ_1:
            self.brains.append(GroqProvider(KEY_GROQ_1, "llama-3.3-70b-versatile", "Groq-70B (Main)"))
        
        # 3. Groq Secundario (Calidad 70B - Refuerzo)
        # Usamos el MISMO modelo potente (70B) porque es una cuenta distinta con sus propios límites.
        if KEY_GROQ_2 and "gsk_" in KEY_GROQ_2:
            self.brains.append(GroqProvider(KEY_GROQ_2, "llama-3.3-70b-versatile", "Groq-70B (Backup)"))

        # 4. Cerebras (Último recurso - Modelo pequeño pero rápido)
        # Solo lo usamos si los tres gigantes fallan.
        if KEY_CEREBRAS and "csk-" in KEY_CEREBRAS:
             self.brains.append(CerebrasProvider(KEY_CEREBRAS, "llama3.1-8b", "Cerebras-8B (Emergency)"))

    def clean_json_markdown(self, text):
        """Limpia los bloques de código ```json que a veces manda la IA"""
        if "```" in text:
            text = re.sub(r"```json", "", text)
            text = re.sub(r"```", "", text)
        return text.strip()

    def audit_contract(self, system_prompt: str, code_snippet: str) -> dict:
        errors = []
        
        for brain in self.brains:
            print(f"[HYDRA] 🔄 Intentando con: {brain.name}...")
            try:
                start_time = time.time()
                
                # LLAMADA A LA IA
                raw_result = brain.analyze(system_prompt, code_snippet)
                
                # LIMPIEZA DE FORMATO
                clean_result = self.clean_json_markdown(raw_result)
                
                latency = round(time.time() - start_time, 2)
                
                print(f"[HYDRA] ✅ ÉXITO con {brain.name} ({latency}s)")
                return {
                    "success": True, 
                    "provider": brain.name,
                    "latency": latency, 
                    "content": clean_result
                }

            except Exception as e:
                error_msg = f"❌ Fallo en {brain.name}: {str(e)}"
                print(error_msg)
                errors.append(error_msg)
                continue # Salta al siguiente cerebro

        # Si llegamos aquí, es el fin...
        print("💀 [HYDRA] FATAL: Todos los proveedores caídos.")
        raise Exception(f"Servicio no disponible. Intentos fallidos: {errors}")