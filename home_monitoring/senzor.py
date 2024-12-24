from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import Column, Integer, Float, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

# PŘEPÍNAČ: True = používá paměť, False = používá databázi
USE_MEMORY = False

# Model pro příchozí data
class SensorDataInput(BaseModel):
    temperature: float = Field(..., ge=-50.0, le=100.0, description="Teplota v rozsahu -50 až 100 °C")
    humidity: float = Field(..., ge=0.0, le=100.0, description="Vlhkost v rozsahu 0 až 100 %")
    sensor_type: Optional[str] = Field("general", description="Typ senzoru")

    @validator("sensor_type")
    def validate_sensor_type(cls, value):
        allowed_types = ["general", "air_quality", "temperature", "humidity"]
        if value not in allowed_types:
            raise ValueError(f"sensor_type must be one of {allowed_types}")
        return value

# Paměťové uložiště (pouze pokud není databáze)
if USE_MEMORY:
    data_store: List[SensorDataInput] = []

# SQLAlchemy - nastavení databáze
DATABASE_URL = "postgresql://postgres:password@localhost/sensor_data"  # Upravit podle svého přístupu
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Model pro databázovou tabulku
if not USE_MEMORY:
    class SensorData(Base):
        __tablename__ = "sensor_data"

        id = Column(Integer, primary_key=True, index=True)
        temperature = Column(Float, nullable=False)
        humidity = Column(Float, nullable=False)
        sensor_type = Column(String, default="general")
        timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Inicializace tabulky
    Base.metadata.create_all(bind=engine)

# FastAPI aplikace
app = FastAPI()

# Závislost na databázové session (pouze pokud databáze)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint pro přidání dat
@app.post("/data")
def add_data(sensor_data: SensorDataInput, db: Session = Depends(get_db if not USE_MEMORY else lambda: None)):
    if USE_MEMORY:
        # Uložení do paměti
        data_store.append(sensor_data)
        return {"message": "Data saved (memory)", "data": sensor_data}
    else:
        # Uložení do databáze
        db_data = SensorData(
            temperature=sensor_data.temperature,
            humidity=sensor_data.humidity,
            sensor_type=sensor_data.sensor_type
        )
        db.add(db_data)
        db.commit()
        db.refresh(db_data)
        return {"message": "Data saved (database)", "data": db_data}

# Endpoint pro získání všech dat
@app.get("/data")
def get_data(db: Session = Depends(get_db if not USE_MEMORY else lambda: None)):
    if USE_MEMORY:
        # Získání dat z paměti
        return {"data": data_store}
    else:
        # Získání dat z databáze
        data = db.query(SensorData).all()
        return {"data": data}

# Endpoint pro získání dat podle času
@app.get("/data/filter")
def get_data_by_time(start: datetime, end: datetime, db: Session = Depends(get_db if not USE_MEMORY else lambda: None)):
    if USE_MEMORY:
        raise HTTPException(status_code=400, detail="Filtering by time is not supported in memory mode")
    else:
        data = db.query(SensorData).filter(SensorData.timestamp >= start, SensorData.timestamp <= end).all()
        return {"data": data}

# Endpoint pro získání posledního záznamu
@app.get("/data/latest")
def get_latest_data(db: Session = Depends(get_db if not USE_MEMORY else lambda: None)):
    if USE_MEMORY:
        if not data_store:
            return {"message": "No data available"}
        return {"data": data_store[-1]}
    else:
        data = db.query(SensorData).order_by(SensorData.timestamp.desc()).first()
        if not data:
            return {"message": "No data available"}
        return {"data": data}

# Volitelně: Kontrolní endpoint
@app.get("/")
def root():
    return {"message": f"API is running (mode: {'memory' if USE_MEMORY else 'database'})"}
