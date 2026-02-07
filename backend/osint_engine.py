import requests
import urllib.parse
import json

class OSINT_Engine:
    def __init__(self):
        # Cabecera para parecer un navegador real
        self.headers = {
            'User-Agent': 'ChainGuard-TFG/3.0 (Educational Security Research)',
            'Accept': 'application/json'
        }

    # --- MÓDULO 1: RASTREO DE IDENTIDAD (PERSONAS / WALLETS) ---
    def investigar_usuario(self, target):
        """Busca huella digital en Web2 adaptando la estrategia al tipo de objetivo."""
        print(f"[OSINT] Iniciando búsqueda de perfil para: {target}")
        
        query = urllib.parse.quote(target)
        dorks = []

        # ESTRATEGIA A: Si es una Dirección (0x...) -> Búsqueda Híbrida (Wallet + Proyecto)
        if target.startswith("0x") and len(target) > 30:
            dorks = [
                # --- RASTREO FINANCIERO (Wallet/Creador) ---
                {"plataforma": "Debank (Portfolio)", "url": f"https://debank.com/profile/{target}"},
                {"plataforma": "OpenSea (NFTs)", "url": f"https://opensea.io/{target}"},
                
                # --- INTELIGENCIA DE PROYECTO (Contrato) ---
                # Estos links usan la Address, son infalibles para ver código/txs
                {"plataforma": "💻 GitHub (Code Search)", "url": f"https://github.com/search?q={query}&type=code"},
                {"plataforma": "🔎 Twitter (Address)", "url": f"https://twitter.com/search?q={query}&src=typed_query"},
            ]
            
            # Herramientas Manuales específicas para Contratos
            herramientas_extra = {
                "Arkham": f"https://platform.arkhamintelligence.com/explorer/address/{target}",
                "Etherscan": f"https://etherscan.io/address/{target}#comments",
                "Tenderly": f"https://dashboard.tenderly.co/contract/mainnet/{target}",
                "Dextools": f"https://www.dextools.io/app/en/search?c={target}"
            }
        
        # ESTRATEGIA B: Si es un Nombre de Usuario (ej: vitalik)
        else:
            dorks = [
                {"plataforma": "LinkedIn", "url": f"https://www.google.com/search?q=site:linkedin.com/in/+OR+site:linkedin.com/pub/+{query}"},
                {"plataforma": "Twitter / X", "url": f"https://www.google.com/search?q=site:twitter.com+{query}"},
                {"plataforma": "GitHub", "url": f"https://www.google.com/search?q=site:github.com+{query}"},
                {"plataforma": "Reddit", "url": f"https://www.google.com/search?q=site:reddit.com/user/+{query}"},
                {"plataforma": "Telegram", "url": f"https://www.google.com/search?q=site:t.me/+{query}"},
                {"plataforma": "Noticias Crypto", "url": f"https://www.google.com/search?q={query}+crypto+scam+OR+hack"},
            ]
            herramientas_extra = {
                "Arkham": "https://platform.arkhamintelligence.com/",
                "Sherlock": "https://app.sherlock.xyz/" 
             }
        
        # 2. Identidad Web3 (ENS Check)
        identidad_web3 = {"ENS": "No detectado", "estado": "N/A"}
        try:
            if not target.startswith("0x"):
                 res = requests.get(f"https://{target}.eth.limo", timeout=3)
                 if res.status_code < 500:
                    identidad_web3 = {
                        "ENS": f"{target}.eth",
                        "estado": "REGISTRADO ✅",
                        "link": f"https://app.ens.domains/{target}.eth"
                    }
        except: pass

        return {
            "huella_digital_web2": dorks,
            "identidad_web3": identidad_web3,
            "herramientas_manuales": {
                "Arkham Intelligence": f"https://platform.arkhamintelligence.com/explorer/address/{target}" if target.startswith("0x") else "https://platform.arkhamintelligence.com/",
                "Blockscan": f"https://blockscan.com/address/{target}"
            }
        }
    
    # --- MÓDULO 2: ANÁLISIS WEB (DOMINIOS) ---
    def analizar_dominio(self, domain):
        """Analiza reputación de dominios usando fuentes externas."""
        print(f"[OSINT] Analizando dominio: {domain}")
        domain = domain.replace("https://", "").replace("http://", "").split('/')[0]

        return {
            "info_registro": {
                "registrador": "Consultar Whois (Link abajo)",
                "fecha_creacion": "Ver en VirusTotal"
            },
            "herramientas_manuales": {
                "🛡️ VirusTotal": f"https://www.virustotal.com/gui/domain/{domain}",
                "🌍 Whois Lookup": f"https://who.is/whois/{domain}",
                "Wayback Machine": f"https://web.archive.org/web/*/{domain}"
            }
        }

    # --- MÓDULO 3: SEGURIDAD DE TOKENS (GOPLUS API + SMART INTEL V4.2) ---
    def analizar_token_goplus(self, address, chain_id):
        """
        Consulta GoPlus y genera Inteligencia basada en NOMBRE y DIRECCIÓN.
        """
        print(f"[OSINT] Consultando GoPlus Security para {address} en Chain {chain_id}...")
        
        url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={address}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            data = response.json()
            
            if data['code'] != 1: return {"error": "GoPlus no respondió datos válidos."}
            
            result = data['result'].get(address.lower())
            if not result: return {"error": "Token no indexado en GoPlus aún."}

            # 1. DATOS BÁSICOS & ARREGLO DE NOMBRE
            token_name = result.get('token_name', '')
            token_symbol = result.get('token_symbol', '???')

            # 🔥 FIX VITAL: Si no hay nombre, usamos el símbolo para que los links no exploten
            search_term = token_name
            if not search_term or search_term.lower() in ["unknown", "desconocido", "none", ""]:
                search_term = token_symbol 
            
            # Limpieza para URL
            safe_name = urllib.parse.quote(search_term.strip())
            
            # --- ANÁLISIS DE RIESGOS ---
            riesgos = []
            is_honeypot = result.get('is_honeypot', '0')
            if is_honeypot == "1": riesgos.append("🚨 HONEYPOT DETECTADO (No se puede vender)")
            if result.get('is_blacklisted') == "1": riesgos.append("⚠️ Función de Blacklist detectada")
            if result.get('is_open_source') == "0": riesgos.append("⚠️ Contrato NO verificado (Código Oculto)")
            if result.get('owner_change_balance') == "1": riesgos.append("🚨 EL DUEÑO PUEDE ALTERAR SALDOS")

            buy_tax = str(float(result.get('buy_tax', 0)) * 100)
            sell_tax = str(float(result.get('sell_tax', 0)) * 100)
            if float(buy_tax) > 10 or float(sell_tax) > 10:
                riesgos.append(f"💸 Impuestos Altos (Compra: {buy_tax}% / Venta: {sell_tax}%)")

            # --- WHALE WATCHER ---
            holders = result.get('holders', [])
            top_10_percentage = 0.0
            whale_warning = False
            if holders:
                for h in holders[:10]:
                    try: top_10_percentage += float(h.get('percent', 0)) * 100
                    except: pass
                top_10_percentage = round(top_10_percentage, 2)
                if top_10_percentage > 50:
                    riesgos.append(f"🐋 RIESGO DE BALLENAS: Top 10 posee el {top_10_percentage}%")
                    whale_warning = True

            # --- 🧠 INTELIGENCIA DE PROYECTO (LINK FIX V4.2) ---
            # Aquí están los links corregidos. Dune directo y Twitter Cashtag.
            project_intel = [
                {"plataforma": "📊 Dune Dashboards", "url": f"https://dune.com/browse/dashboards?q={safe_name}"},
                {"plataforma": "🐦 Twitter Sentiment", "url": f"https://twitter.com/search?q=%24{token_symbol}&src=typed_query"}, # Busca $TICKER
                {"plataforma": "💀 Rekt.news (Hacks)", "url": f"https://www.google.com/search?q=site:rekt.news+%22{safe_name}%22"},
                {"plataforma": "🐛 Immunefi (Bounty)", "url": f"https://www.google.com/search?q=site:immunefi.com+%22{safe_name}%22"},
                {"plataforma": "📰 Noticias (Google)", "url": f"https://www.google.com/search?q=\"{safe_name}\"+crypto+scam+OR+hack"}
            ]

            # Estructura de retorno
            return {
                "es_token": True,
                "nombre": token_name,
                "simbolo": token_symbol,
                "honeypot": "SÍ" if is_honeypot == "1" else "NO",
                "impuestos": f"Buy: {buy_tax}% | Sell: {sell_tax}%",
                "dueño_renunciado": "NO" if result.get('owner_address') != "" else "SÍ (Renunciado)",
                "riesgos_detectados": riesgos,
                
                "whales_info": {
                    "top_10_percent": f"{top_10_percentage}%",
                    "is_centralized": whale_warning
                },

                "project_intel": project_intel, 
                
                "link_goplus": f"https://gopluslabs.io/token-security/{chain_id}/{address}",
                "creador_address": result.get('creator_address', None)
            }

        except Exception as e:
            print(f"[ERROR OSINT] {e}")
            return {"error": f"Fallo de conexión GoPlus: {str(e)}"}