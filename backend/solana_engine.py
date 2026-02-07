import requests
import json

class SolanaRPCEngine:
    def __init__(self):
        # Usamos el RPC público de Solana. 
        # NOTA: En producción real, usar QuickNode o Helius para evitar rate-limits.
        self.rpc_url = "https://api.mainnet-beta.solana.com"
        self.headers = {"Content-Type": "application/json"}

    def _rpc_call(self, method, params):
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        try:
            response = requests.post(self.rpc_url, headers=self.headers, json=payload, timeout=5)
            return response.json()
        except Exception as e:
            print(f"[SOLANA RPC] Error de conexión: {e}")
            return None

    def analizar_token(self, token_address):
        """
        Consulta la blockchain para ver las 'Autoridades' (Permisos Críticos) del token.
        """
        print(f"[SOLANA] Analizando permisos on-chain para: {token_address}")
        
        # 1. Obtener información de la cuenta (Account Info) con encoding jsonParsed
        data = self._rpc_call("getAccountInfo", [
            token_address,
            {"encoding": "jsonParsed"}
        ])

        # Verificaciones básicas de que existe
        if not data or 'result' not in data or 'value' not in data['result'] or data['result']['value'] is None:
            return {"error": "Dirección no encontrada o no es una cuenta activa en Solana."}

        try:
            # Intentamos parsear como Token SPL
            val = data['result']['value']
            if 'data' in val and 'parsed' in val['data'] and 'info' in val['data']['parsed']:
                parsed_data = val['data']['parsed']['info']
            else:
                return {"error": "No es un Token SPL estándar (puede ser una Wallet o Programa custom)."}
            
            # 2. Extracción de Autoridades (LAS LLAVES DEL REINO)
            mint_authority = parsed_data.get('mintAuthority')
            freeze_authority = parsed_data.get('freezeAuthority')
            supply = parsed_data.get('supply', '0')
            decimals = parsed_data.get('decimals', 0)

            riesgos = []
            info_extra = []
            
            # --- ANÁLISIS TÁCTICO ---
            
            # A. MINT (¿Pueden imprimir dinero infinito?)
            if mint_authority:
                riesgos.append(f"🚨 MINT AUTHORITY ACTIVA: La wallet {mint_authority[:6]}... puede imprimir tokens infinitos.")
                info_extra.append(f"- Mint Auth: ACTIVA ({mint_authority})")
            else:
                info_extra.append("- Mint Auth: RENUNCIADA (Seguro) ✅")

            # B. FREEZE (¿Pueden congelar tu dinero?)
            if freeze_authority:
                riesgos.append(f"❄️ FREEZE AUTHORITY ACTIVA: La wallet {freeze_authority[:6]}... puede congelar carteras.")
                info_extra.append(f"- Freeze Auth: ACTIVA ({freeze_authority})")
            else:
                info_extra.append("- Freeze Auth: DESACTIVADA (Seguro) ✅")

            return {
                "success": True,
                "riesgos": riesgos,
                "info_tecnica": "\n".join(info_extra),
                "supply": supply
            }

        except Exception as e:
            return {"error": f"Error parseando datos Solana: {str(e)}"}