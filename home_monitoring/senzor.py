# PŘÍPRAVA BACKENDU:from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import Column, Integer, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base #knihgovna pro práci s databází
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List 

# PŘEPÍNAČ: True = používá paměť, False = používá databázi
USE_MEMORY = False

# Model pro příchozí data
class SensorDataInput(BaseModel):
    temperature: float
    humidity: float

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
        # Uložení do databáze ->
        db_data = SensorData(temperature=sensor_data.temperature, humidity=sensor_data.humidity)
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

# Volitelně: Kontrolní endpoint
@app.get("/")
def root():
    return {"message": f"API is running (mode: {'memory' if USE_MEMORY else 'database'})"}
