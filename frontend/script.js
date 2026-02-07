// script.js - ChainGuard V4.0 (Smart Intel Edition)

// --- 1. REFERENCIAS AL DOM ---
const inputField = document.getElementById("main-input");
const btnAction = document.querySelector(".btn-audit");
const resultArea = document.getElementById("result-area");
const chainSelector = document.getElementById("chain-selector");
const btnPdf = document.getElementById("btn-download-pdf");

// Elementos internos del resultado
const resHeader = document.getElementById("res-header");
const resTitle = document.getElementById("res-title");
const resDesc = document.getElementById("res-desc");
const resDetails = document.getElementById("res-details");
const resWrapper = document.getElementById("res-content-wrapper");

// --- ESTADO GLOBAL ---
window.currentMode = 'audit'; 
let lastAuditData = null;

// --- 2. INICIALIZACIÓN ---
document.addEventListener("DOMContentLoaded", () => {
    // Inicializar visualmente en modo audit
    if(typeof setMode === "function") setMode('audit'); 
});

// --- 3. LÓGICA DEL BOTÓN PRINCIPAL ---
if (btnAction) {
    btnAction.addEventListener("click", async () => {
        const target = inputField.value.trim();
        if (!target) {
            showError("⚠️ El campo está vacío. Introduce un contrato o usuario.");
            return;
        }

        const mode = window.currentMode;

        // UI de Carga
        setLoading(true);
        clearResults();

        try {
            let endpoint = mode === 'audit' ? 'audit_proxy.php' : 'osint_proxy.php';
            const selectedChain = chainSelector ? chainSelector.value : '1';

            // Payload dinámico
            let payload = { 
                [mode === 'audit' ? 'contract' : 'target']: target,
                chain: selectedChain 
            };

            console.log(`[JS] Modo: ${mode} | Enviando a ${endpoint}...`, payload);

            const response = await fetch(endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            // --- JSON CLEANER ---
            const text = await response.text();
            let data;
            try {
                const jsonStart = text.indexOf('{');
                const jsonEnd = text.lastIndexOf('}') + 1;
                if (jsonStart !== -1 && jsonEnd !== -1) {
                    data = JSON.parse(text.substring(jsonStart, jsonEnd));
                } else {
                    throw new Error("Respuesta no válida del servidor");
                }
            } catch (e) {
                console.error("JSON Raw:", text);
                throw new Error("Error parseando respuesta del servidor.");
            }

            // PROCESAR RESULTADO
            if (data.status === "error" || data.error) {
                showError(data.error || "Error desconocido.");
            } else {
                lastAuditData = data; // Guardar para PDF
                
                if (mode === 'audit') {
                    renderAuditResult(data);
                } else {
                    renderOsintResult(data);
                }
            }

        } catch (error) {
            console.error("[JS] Error:", error);
            showError(`Error de conexión: ${error.message}`);
        } finally {
            setLoading(false);
        }
    });
}

// --- 4. RENDERIZADO AUDITORÍA ---
function renderAuditResult(data) {
    resHeader.style.display = "block";
    
    // Determinar colores y riesgo
    let riskNum = 0;
    if(data.riesgo) riskNum = parseInt(data.riesgo.toString().replace(/\D/g, ''));

    let colorClass = "text-green-400";
    let icon = "check_circle";

    if (riskNum > 75) { 
        colorClass = "text-alert"; 
        icon = "warning"; 
    } else if (riskNum > 40) { 
        colorClass = "text-yellow-400"; 
        icon = "error"; 
    }

    resTitle.innerHTML = `
        <div class="flex items-center gap-3">
            <span class="material-symbols-outlined ${colorClass} text-3xl">${icon}</span>
            <div class="flex flex-col">
                <span class="${colorClass} text-xl font-bold tracking-wide">${data.risk_level || "ANÁLISIS COMPLETADO"}</span>
                <span class="text-xs text-slate-500 uppercase tracking-widest">Confidence Score: High</span>
            </div>
        </div>
    `;

    resDesc.innerHTML = `
        <div class="mt-2 flex items-center gap-2 text-sm text-slate-400">
            <span class="material-symbols-outlined text-sm">hub</span> Fuente: 
            <span class="text-white bg-white/10 px-2 py-0.5 rounded font-mono">${data.source || 'Desconocida'}</span>
        </div>
    `;

    resDetails.innerHTML = formatMarkdown(data.details);
    if(btnPdf) btnPdf.style.display = "flex";
}

// --- 5. RENDERIZADO OSINT (INTELIGENCIA HÍBRIDA) ---
function renderOsintResult(data) {
    resHeader.style.display = "block";
    
    // Cabecera OSINT
    resTitle.innerHTML = `
        <div class="flex items-center gap-4 mb-2">
            <div class="p-3 bg-blue-500/10 rounded-lg border border-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.3)]">
                <span class="material-symbols-outlined text-blue-400 text-3xl animate-pulse">policy</span>
            </div>
            <div class="flex flex-col">
                <span class="text-blue-400 text-xl font-bold tracking-wide font-display">REPORTE DE INTELIGENCIA</span>
                <span class="text-xs text-slate-500 uppercase tracking-widest font-mono">Target: ${inputField.value}</span>
            </div>
        </div>
    `;
    resDesc.innerHTML = ""; 

    let html = "";
    const d = data.datos || {}; 

    // === A. ANÁLISIS DE TOKEN + BALLENAS ===
    if (d.es_token) {
        const isHoneypot = d.honeypot === 'SÍ' || d.honeypot === 'YES';
        const hpColor = isHoneypot ? 'text-alert' : 'text-green-400';
        const hpIcon = isHoneypot ? 'warning' : 'verified_user';
        const hpText = isHoneypot ? 'HONEYPOT DETECTADO' : 'NO ES HONEYPOT';
        const hpBorder = isHoneypot ? 'border-alert/50 shadow-[0_0_20px_rgba(239,68,68,0.2)]' : 'border-green-500/30';

        html += `
            <div class="mb-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div class="flex justify-between items-end mb-2">
                    <h4 class="text-slate-300 text-xs font-bold uppercase tracking-wider flex items-center gap-2">
                        <span class="material-symbols-outlined text-primary text-sm">token</span> Análisis de Activo
                    </h4>
                    <span class="text-[10px] bg-white/5 px-2 py-0.5 rounded text-slate-500 border border-white/5">GoPlus Security API</span>
                </div>
                
                <div class="bg-[#0f0f0f] p-5 rounded-xl border ${hpBorder} relative overflow-hidden group">
                    <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0IiBoZWlnaHQ9IjQiPgo8cmVjdCB3aWR0aD0iNCIgaGVpZ2h0PSI0IiBmaWxsPSIjZmZmIiBmaWxsLW9wYWNpdHk9IjAuMDIiLz4KPC9zdmc+')] opacity-20"></div>
                    
                    <div class="flex justify-between items-start mb-4 relative z-10">
                        <div>
                            <div class="text-2xl font-bold text-white tracking-tight">${d.nombre} <span class="text-slate-500 text-lg font-normal">(${d.simbolo})</span></div>
                            <div class="flex gap-2 mt-1">
                                <span class="text-xs font-mono bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded border border-blue-500/20">ERC-20</span>
                                <span class="text-xs font-mono bg-purple-500/10 text-purple-400 px-2 py-0.5 rounded border border-purple-500/20">Supply: Variable</span>
                            </div>
                        </div>
                        <div class="flex flex-col items-end">
                            <div class="flex items-center gap-1 ${hpColor} font-bold text-sm bg-black/40 px-3 py-1 rounded-full border border-white/10">
                                <span class="material-symbols-outlined text-sm">${hpIcon}</span> ${hpText}
                            </div>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-4 text-sm border-t border-white/5 pt-4 relative z-10">
                        <div>
                            <span class="text-slate-500 text-xs block mb-1">Impuestos (Buy/Sell)</span>
                            <span class="text-white font-mono text-lg">${d.impuestos || "Unknown"}</span>
                        </div>
                        <div>
                            <span class="text-slate-500 text-xs block mb-1">Estado de Propiedad</span>
                            <span class="text-white font-mono">${d.dueño_renunciado === 'SÍ' ? 'Renunciado ✅' : '<span class="text-orange-400">Tiene Dueño ⚠️</span>'}</span>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-4 text-sm border-t border-white/5 pt-4 mt-2 relative z-10">
                         <div>
                            <span class="text-slate-500 text-xs block mb-1">Top 10 Holders</span>
                            <span class="${d.whales_info?.is_centralized ? 'text-orange-400' : 'text-green-400'} font-mono text-lg">
                                ${d.whales_info?.top_10_percent || "0%"}
                            </span>
                        </div>
                        <div>
                             <span class="text-slate-500 text-xs block mb-1">Creador</span>
                             <a href="#" onclick="navigator.clipboard.writeText('${d.creador_address}'); return false;" class="text-blue-400 hover:text-white font-mono text-xs truncate w-full block transition-colors" title="Copiar Dirección">
                                ${d.creador_address ? d.creador_address.substring(0,8)+'...'+d.creador_address.substring(38) : 'Desconocido'} ❐
                             </a>
                        </div>
                    </div>
                </div>
        `;

        // Riesgos Críticos
        if (d.riesgos_detectados && d.riesgos_detectados.length > 0) {
            html += `<div class="mt-3 bg-alert/5 border border-alert/20 rounded-lg p-3 relative overflow-hidden">
                        <div class="absolute left-0 top-0 bottom-0 w-1 bg-alert"></div>
                        <div class="text-alert font-bold text-xs mb-2 uppercase flex items-center gap-2">
                            <span class="material-symbols-outlined text-sm">bug_report</span> Riesgos Críticos
                        </div>
                        <ul class="space-y-1">`;
            d.riesgos_detectados.forEach(r => {
                html += `<li class="text-red-300 text-xs flex items-start gap-2">
                            <span class="text-alert mt-0.5">›</span> ${r}
                         </li>`;
            });
            html += `</ul></div>`;
        }
        html += `</div>`; 
    }

    // === B. INTELIGENCIA DE PROYECTO (SMART LINKS - AZUL) ===
    if (d.project_intel && d.project_intel.length > 0) {
        html += `
            <div class="mb-6 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
                <h4 class="text-slate-300 text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-2">
                    <span class="material-symbols-outlined text-blue-400 text-sm">travel_explore</span> Investigación de Proyecto ("${d.nombre || 'Target'}")
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2">`;
        
        d.project_intel.forEach(item => {
            html += `
                <a href="${item.url}" target="_blank" class="flex items-center justify-between bg-[#111] hover:bg-[#1a1a1a] p-3 rounded-lg border border-white/5 hover:border-blue-500/30 transition-all group">
                    <div class="flex items-center gap-3">
                        <div class="size-2 rounded-full bg-blue-500 group-hover:shadow-[0_0_8px_#3b82f6]"></div>
                        <span class="text-slate-300 text-sm font-medium group-hover:text-white">${item.plataforma}</span>
                    </div>
                    <span class="material-symbols-outlined text-xs text-slate-600 group-hover:text-blue-400 transition-colors">open_in_new</span>
                </a>`;
        });
        html += `</div></div>`;
    }

    // === C. HUELLA DEL CREADOR / WALLET (VIOLETA) ===
    if (d.huella_digital_web2 && d.huella_digital_web2.length > 0) {
         html += `
            <div class="mb-6 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200">
                <h4 class="text-slate-300 text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-2">
                    <span class="material-symbols-outlined text-purple-400 text-sm">person_search</span> Huella del Creador / Wallet
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2">`;
        d.huella_digital_web2.forEach(item => {
             html += `
                <a href="${item.url}" target="_blank" class="flex items-center justify-between bg-[#111] hover:bg-[#1a1a1a] p-3 rounded-lg border border-white/5 hover:border-purple-500/30 transition-all group">
                    <div class="flex items-center gap-3">
                        <div class="size-2 rounded-full bg-purple-500 group-hover:shadow-[0_0_8px_#a855f7]"></div>
                        <span class="text-slate-300 text-sm font-medium group-hover:text-white">${item.plataforma}</span>
                    </div>
                    <span class="material-symbols-outlined text-xs text-slate-600 group-hover:text-purple-400 transition-colors">open_in_new</span>
                </a>`;
        });
        html += `</div></div>`;
    }

    // === D. IDENTIDAD ON-CHAIN (ENS) ===
    if (d.identidad_web3 && d.identidad_web3.ENS) {
        html += `
            <div class="mb-6 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200">
                 <h4 class="text-slate-300 text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-2">
                    <span class="material-symbols-outlined text-purple-400 text-sm">fingerprint</span> Identidad On-Chain
                </h4>
                <div class="bg-gradient-to-r from-purple-900/20 to-blue-900/10 p-4 rounded-xl border border-purple-500/20 flex items-center gap-4 relative overflow-hidden">
                    <div class="absolute -right-10 -top-10 size-32 bg-purple-500/10 rounded-full blur-2xl"></div>
                    <div class="size-12 bg-black/40 rounded-full flex items-center justify-center text-2xl border border-white/10 shadow-inner">💎</div>
                    <div>
                        <div class="text-white font-bold text-lg tracking-tight">${d.identidad_web3.ENS}</div>
                        <div class="flex items-center gap-2 mt-1">
                            <span class="text-[10px] text-green-400 bg-green-500/10 px-1.5 py-0.5 rounded uppercase font-bold tracking-wider">Active</span>
                            <span class="text-[10px] text-slate-500 font-mono">${d.identidad_web3.estado}</span>
                        </div>
                    </div>
                </div>
            </div>`;
    } 
    // Si NO hay identidad (DEV ANÓNIMO)
    else if (d.es_token) {
         html += `
            <div class="mb-6 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200">
                 <h4 class="text-slate-300 text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-2">
                    <span class="material-symbols-outlined text-slate-500 text-sm">fingerprint</span> Identidad On-Chain
                </h4>
                <div class="bg-[#111] p-4 rounded-xl border border-white/5 flex items-center gap-4">
                    <div class="size-10 bg-black/40 rounded-full flex items-center justify-center text-xl text-slate-600">🕵️</div>
                    <div>
                        <div class="text-slate-400 font-bold text-sm">Identidad Desconocida</div>
                        <div class="text-[10px] text-orange-400 mt-0.5 flex items-center gap-1">
                            <span class="material-symbols-outlined text-[10px]">warning</span> Riesgo de Anonimato
                        </div>
                    </div>
                </div>
            </div>`;
    }

    // === E. LINKS MANUALES (TOOLS) ===
    if (d.herramientas_manuales) {
        html += `<div class="mt-6 pt-4 border-t border-white/5 animate-in fade-in duration-1000">
                 <div class="text-[10px] text-slate-600 mb-2 uppercase tracking-widest font-bold">Herramientas Externas</div>
                 <div class="flex flex-wrap gap-2">`;
        for (const [key, val] of Object.entries(d.herramientas_manuales)) {
            html += `<a href="${val}" target="_blank" class="text-xs bg-black hover:bg-white/5 border border-white/10 px-3 py-1.5 rounded-md text-slate-400 hover:text-white hover:border-primary transition-all flex items-center gap-2">
                        ${key} <span class="material-symbols-outlined text-[10px]">arrow_outward</span>
                     </a>`;
        }
        html += `</div></div>`;
    }

    // Fallback
    if (!html) {
         html = `<div class="flex flex-col items-center justify-center py-12 text-slate-500">
                    <span class="material-symbols-outlined text-4xl mb-2 opacity-50">search_off</span>
                    <p class="text-sm">No se encontraron datos OSINT públicos relevantes.</p>
                </div>`;
    }
    resDetails.innerHTML = html;
    if(btnPdf) btnPdf.style.display = "flex";
}

// --- 6. GENERACIÓN PDF ---
if(btnPdf){
    btnPdf.addEventListener("click", async () => {
        if (!lastAuditData) return;
        const originalContent = btnPdf.innerHTML;
        btnPdf.innerHTML = `<span class="material-symbols-outlined animate-spin text-sm">sync</span> Generando...`;
        
        try {
            const response = await fetch('report_proxy.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(lastAuditData)
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `ChainCortex_Report_${Date.now()}.pdf`;
                document.body.appendChild(a);
                a.click();
                a.remove();
            } else {
                alert("Error generando PDF");
            }
        } catch (e) {
            console.error(e);
            alert("Error de conexión (PDF)");
        } finally {
            btnPdf.innerHTML = originalContent;
        }
    });
}

// --- HELPERS VISUALES ---
function setLoading(isLoading) {
    if (isLoading) {
        btnAction.innerHTML = `<span class="material-symbols-outlined animate-spin">progress_activity</span> PROCESANDO...`;
        btnAction.classList.add("opacity-75", "cursor-not-allowed");
        resHeader.style.display = "none";
        resDetails.innerHTML = `
            <div class="flex flex-col items-center justify-center h-48 gap-4 opacity-50">
                <span class="material-symbols-outlined text-4xl animate-bounce text-primary">radar</span>
                <span class="font-mono text-sm animate-pulse">Interceptando señales en la blockchain...</span>
            </div>
        `;
    } else {
        const mode = window.currentMode;
        const icon = mode === 'audit' ? 'bolt' : 'search';
        const text = mode === 'audit' ? 'AUDITAR CÓDIGO' : 'INVESTIGAR OBJETIVO';
        btnAction.innerHTML = `<span class="material-symbols-outlined group-hover:rotate-90 transition-transform">${icon}</span> ${text}`;
        btnAction.classList.remove("opacity-75", "cursor-not-allowed");
    }
}

function clearResults() {
    resHeader.style.display = "none";
    resDetails.innerHTML = "";
    if(btnPdf) btnPdf.style.display = "none";
}

function showError(msg) {
    resHeader.style.display = "block";
    resTitle.innerHTML = `<div class="text-alert flex items-center gap-2"><span class="material-symbols-outlined">error</span> ERROR DEL SISTEMA</div>`;
    resDesc.innerText = "";
    resDetails.innerHTML = `<div class="bg-alert/10 border border-alert/20 p-4 rounded text-alert font-mono text-sm">${msg}</div>`;
}

function formatMarkdown(text) {
    if (!text) return "";
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white">$1</strong>')
        .replace(/`(.*?)`/g, '<code class="bg-white/10 px-1.5 py-0.5 rounded text-primary font-mono text-xs">$1</code>')
        .replace(/\n/g, '<br>');
}