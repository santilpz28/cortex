<?php
ini_set('max_execution_time', 300); // 300 segundos = 5 minutos de espera
set_time_limit(300);

header('Content-Type: application/json');

// 1. Recibir datos del JS
$inputJSON = file_get_contents('php://input');
$input = json_decode($inputJSON, true);

if (!isset($input['target']) || empty($input['target'])) {
    echo json_encode(['error' => 'Objetivo vacío']);
    exit();
}

// --- NUEVO: Capturar el ID de la Red ---
// Si el JS no lo manda, usamos '1' (Ethereum) por defecto
$chainId = $input['chain'] ?? '1';

// 2. ENVIAR A WINDOWS (Tu Backend OSINT)
$api_host = getenv('API_URL') ?: 'http://backend:8000';
$url = $api_host . '/investigar';
// $url = 'http://192.168.106.1:8000/investigar'; // ⚠️ Verifica tu IP siempre

// --- NUEVO: Payload con chain_id incluido ---
$payload = json_encode([
    'target' => $input['target'],
    'chain_id' => $chainId
]);

$ch = curl_init($url);
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, $payload); // Enviamos el nuevo paquete
curl_setopt($ch, CURLOPT_HTTPHEADER, array('Content-Type: application/json'));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

// 3. Devolver respuesta
if ($http_code === 200) {
    echo $response;
} else {
    // Si falla, devolvemos info útil
    echo json_encode(["error" => "Error al conectar con el módulo de Inteligencia ($http_code)."]);
}
?>