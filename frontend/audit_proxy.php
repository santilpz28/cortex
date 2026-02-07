<?php
ini_set('max_execution_time', 300); // 300 segundos = 5 minutos de espera
set_time_limit(300);

header('Content-Type: application/json');

// 1. Recibir datos del JS
$inputJSON = file_get_contents('php://input');
$input = json_decode($inputJSON, true);

if (!isset($input['contract']) || empty($input['contract'])) {
    echo json_encode(['status' => 'error', 'error' => 'Código vacío']);
    exit();
}

// --- NUEVO: Capturar el ID de la Red (Chain ID) ---
$chainId = $input['chain'] ?? '1';

// 2. ENVIAR A PYTHON (Conexión Dockerizada)
$payload = json_encode([
    'code_snippet' => $input['contract'],
    'chain_id' => $chainId
]);

// Detecta si estamos en Docker o local
$api_host = getenv('API_URL') ?: 'http://backend:8000';
$url = $api_host . '/auditar';

$ch = curl_init($url);
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
curl_setopt($ch, CURLOPT_HTTPHEADER, array('Content-Type: application/json'));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 60); // Esperamos hasta 60s por la IA

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

// 3. PROCESAR RESPUESTA
if ($http_code === 200) {
    $ai_data = json_decode($response, true);

    // Variables iniciales (Priorizamos lo que viene limpio de Python/DB)
    $veredicto = $ai_data['veredicto'] ?? null;
    $riesgo = $ai_data['riesgo'] ?? null;
    $msg = $ai_data['tipo_vulnerabilidad'] ?? 'Análisis Completo';
    $source = $ai_data['origen_codigo'] ?? 'Desconocido';
    $details = $ai_data['explicacion'] ?? '';
    $linea = $ai_data['linea_afectada'] ?? '';

    // --- PLAN B: SI LA IA NO DEVOLVIÓ JSON LIMPIO (REGEX RESCUE) ---
    if (!$veredicto && isset($ai_data['analisis_raw'])) {
        $raw = $ai_data['analisis_raw'];

        // Intentamos rescatar datos del texto crudo
        if (preg_match('/\*\*Veredicto:\*\*\s*(.*?)(\\n|$)/u', $raw, $m)) $veredicto = trim($m[1]);
        if (preg_match('/\*\*Riesgo:\*\*\s*(\d+)/u', $raw, $m)) $riesgo = trim($m[1]);
        if (preg_match('/\*\*Tipo de vulnerabilidad:\*\*\s*(.*?)(\\n|$)/u', $raw, $m)) $msg = trim($m[1]);

        // Valores por defecto si todo falla
        if (!$veredicto) $veredicto = "PRECAUCIÓN";
        if (!$riesgo) $riesgo = "50";

        // Limpiamos el texto de asteriscos MD para que se vea bien
        $details = str_replace("**", "", $raw);
    }

    // --- LIMPIEZA FINAL DE DATOS ---
    // Aseguramos que el riesgo sea solo un número (quitamos %, símbolos, etc)
    $riesgo = preg_replace('/[^0-9]/', '', $riesgo);

    // Devolver al Frontend formateado
    echo json_encode([
        // Datos para la Web (UI)
        "status" => "success",
        "risk_level" => $veredicto . " (" . $riesgo . "%)",
        "message" => $msg,
        "source" => $source,
        "details" => $details . ($linea ? "\n\n📍 Línea: $linea" : ""),

        // Datos para el PDF
        "veredicto" => $veredicto,
        "riesgo" => $riesgo,
        "tipo_vulnerabilidad" => $msg,
        "origen_codigo" => $source,
        "explicacion" => $details,
        "ubicacion" => $linea
    ]);

} else {
    // Si Python/Docker falla
    echo json_encode(["status" => "error", "error" => "Error de conexión con el Cerebro ($http_code)"]);
}
?>