<?php
// report_proxy.php
// Este proxy maneja la descarga de archivos binarios (PDF)
ini_set('max_execution_time', 300); // 300 segundos = 5 minutos de espera
set_time_limit(300);

// 1. Recibir datos del JS
$inputJSON = file_get_contents('php://input');
$data = json_decode($inputJSON, true);

// 2. Configurar la petición a Python

$api_host = getenv('API_URL') ?: 'http://backend:8000';
$url = $api_host . '/reporte';
//$url = 'http://192.168.106.1:8000/reporte';

$ch = curl_init($url);
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, $inputJSON); // Pasamos el JSON tal cual
curl_setopt($ch, CURLOPT_HTTPHEADER, array('Content-Type: application/json'));
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_BINARYTRANSFER, true); // Importante para archivos
curl_setopt($ch, CURLOPT_TIMEOUT, 60);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$content_type = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);
curl_close($ch);

// 3. Devolver el PDF al navegador
if ($http_code === 200) {
    // Forzamos la cabecera de PDF para que el navegador sepa qué es
    header("Content-Type: application/pdf");
    header("Content-Disposition: attachment; filename=ChainCortex_Reporte.pdf");
    echo $response;
} else {
    // Si falla, devolvemos JSON de error
    header('Content-Type: application/json');
    echo json_encode(["status" => "error", "message" => "Fallo al generar PDF en backend ($http_code)"]);
}
?>