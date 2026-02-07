import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
from datetime import datetime, timedelta  # <--- AÑADIR timedelta

# Configuración de conexión (Lee las variables de Docker)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local_backup.db")

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- MODELO DE LA TABLA (La estructura de los datos) ---
class AuditReport(Base):
    __tablename__ = "audit_reports"

    id = Column(Integer, primary_key=True, index=True)
    contract_address = Column(String, index=True) # Dirección del contrato
    chain_id = Column(String)                     # Red (ETH, BSC...)
    ai_json = Column(Text)                        # El reporte JSON completo
    created_at = Column(DateTime, default=datetime.utcnow) # Fecha

# --- FUNCIONES TÁCTICAS ---

def init_db():
    """Crea las tablas si no existen"""
    Base.metadata.create_all(bind=engine)

def get_cached_audit(address: str, chain: str):
    """Busca si tenemos un reporte de hace MENOS de 24h"""
    db = SessionLocal()
    try:
        # Calculamos la fecha de corte: Ahora menos 24 horas
        limite_tiempo = datetime.utcnow() - timedelta(hours=24)

        # Buscamos reporte que coincida Y sea reciente
        report = db.query(AuditReport).filter(
            AuditReport.contract_address == address,
            AuditReport.chain_id == chain,
            AuditReport.created_at >= limite_tiempo  # <--- FILTRO DE TIEMPO
        ).first()

        if report:
            return json.loads(report.ai_json)
        return None # Si es viejo o no existe, devuelve None (y Python llamará a la IA)
    finally:
        db.close()

def save_audit(address: str, chain: str, data: dict):
    """Guarda el resultado de la IA en la base de datos"""
    db = SessionLocal()
    try:
        # Convertimos el dict a string JSON para guardarlo
        json_str = json.dumps(data)
        new_report = AuditReport(
            contract_address=address,
            chain_id=chain,
            ai_json=json_str
        )
        db.add(new_report)
        db.commit()
        print(f"[DB] 💾 Auditoría guardada para {address}")
    except Exception as e:
        print(f"[DB] ❌ Error guardando: {e}")
    finally:
        db.close()