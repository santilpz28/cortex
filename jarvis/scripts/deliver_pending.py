#!/usr/bin/env python3
"""Consumidor de la cola pending_delivery.json — entrega directa a Telegram.

Diseñado para correr en el servidor del clon (212.227.90.79) como usuario jarvis.
Lee el token del bot desde openclaw.json del clon, envía el reporte + audio a
Santi y marca delivered=True.

Uso: python3 deliver_pending.py [--dry-run] [--limit N]
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime

WORKDIR = "/home/jarvis/.openclaw/workspace"
PENDING_FILE = os.path.join(WORKDIR, "memory", "pending_delivery.json")
CONFIG_FILE = "/home/jarvis/.openclaw/openclaw.json"
LOG_FILE = os.path.join(WORKDIR, "memory", "chainguard_watchdog", "delivery.log")
STATE_FILE = os.path.join(WORKDIR, "memory", "chainguard_watchdog", ".delivery_lock")


def log(msg):
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line, flush=True)


def get_token():
    with open(CONFIG_FILE) as f:
        cfg = json.load(f)
    return cfg["channels"]["telegram"]["botToken"]


def get_chat_id():
    with open(CONFIG_FILE) as f:
        cfg = json.load(f)
    tg = cfg.get("channels", {}).get("telegram", {})
    # allowFrom[0] es el chat_id del usuario (Santi)
    allow = tg.get("allowFrom") or []
    if allow:
        return str(allow[0])
    raise RuntimeError("No chat_id found in config")


def tg_send(token, method, payload):
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def tg_send_doc(token, chat_id, path, caption):
    """Envía un documento (audio o md) multipart."""
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    boundary = "----JARVIS" + str(int(time.time() * 1000))
    fname = os.path.basename(path)
    with open(path, "rb") as f:
        filedata = f.read()
    parts = []
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode())
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode()
    )
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        f'Content-Disposition: form-data; name="document"; filename="{fname}"\r\n'.encode()
    )
    parts.append(b"Content-Type: application/octet-stream\r\n\r\n")
    parts.append(filedata)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(parts)
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode())


def acquire_lock():
    try:
        fd = os.open(STATE_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        # lock viejo > 30 min → stale
        try:
            age = time.time() - os.path.getmtime(STATE_FILE)
            if age > 1800:
                os.unlink(STATE_FILE)
                return acquire_lock()
        except Exception:
            pass
        return False


def release_lock():
    try:
        os.unlink(STATE_FILE)
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    if not os.path.exists(PENDING_FILE):
        log("pending_delivery.json no existe, nada que hacer")
        return 0

    with open(PENDING_FILE) as f:
        data = json.load(f)
    items = data.get("items", []) if isinstance(data, dict) else data
    pending = [i for i in items if not i.get("delivered")]
    log(f"Cola: {len(items)} items, {len(pending)} sin entregar")

    # Deduplicar: la cola acumulo re-ejecuciones del mismo reporte (mismo
    # report_file). Santi no debe recibir 10 veces el mismo W37.
    seen = set()
    deduped = []
    for i in pending:
        key = i.get("report_file") or i.get("timestamp")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(i)
    if len(deduped) != len(pending):
        log(f"Deduplicado: {len(pending)} -> {len(deduped)} reportes unicos")
    pending = deduped

    if args.dry_run:
        for i in pending:
            log(f"[DRY] {i.get('timestamp')} -> {i.get('report_file')}")
        return 0

    if not pending:
        return 0

    if not acquire_lock():
        log("Lock ocupado, otro proceso está entregando. Salindo.")
        return 0

    try:
        token = get_token()
        chat_id = get_chat_id()
        limit = args.limit or len(pending)
        sent = 0
        for item in pending[:limit]:
            report = item.get("report_file")
            audio = item.get("audio_file")
            summary = item.get("summary") or "Reporte semanal ChainGuard"
            try:
                # 1. Texto del reporte (markdown, recortado a 4000 chars)
                text = ""
                if report and os.path.exists(report):
                    with open(report) as f:
                        text = f.read()
                if not text:
                    text = summary
                if len(text) > 4000:
                    text = text[:3900] + "\n\n…(recortado)"
                tg_send(token, "sendMessage", {"chat_id": chat_id, "text": text[:4000]})
                log(f"Enviado texto: {summary}")

                # 2. Audio (voz)
                if audio and os.path.exists(audio):
                    tg_send_doc(token, chat_id, audio, f"🔊 {summary}")
                    log(f"Enviado audio: {os.path.basename(audio)}")

                item["delivered"] = True
                item["delivered_at"] = datetime.now().isoformat(timespec="seconds")
                sent += 1
                time.sleep(2)  # rate-limit conservador
            except Exception as e:
                log(f"ERROR enviando {summary}: {e}")
                break

        # Reescribir cola solo si es lista plana; si es dict con items, preservamos
        if sent:
            with open(PENDING_FILE, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log(f"Completado: {sent} entregados, {len(pending) - sent} restantes")
    finally:
        release_lock()
    return 0


if __name__ == "__main__":
    sys.exit(main())
