from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Personaje, Mision, MisionPersonaje
from database import get_db, crear_base_datos

app = FastAPI(title="Sistema de Misiones RPG")

crear_base_datos()

@app.post("/personajes")
def crear_personaje(nombre: str, db: Session = Depends(get_db)):
    personaje = Personaje(nombre=nombre)
    db.add(personaje)
    db.commit()
    db.refresh(personaje)
    return personaje

@app.post("/misiones")
def crear_mision(nombre: str, descripcion: str = "", experiencia: int = 0, db: Session = Depends(get_db)):
    mision = Mision(nombre=nombre, descripcion=descripcion, experiencia=experiencia, estado='pendiente')
    db.add(mision)
    db.commit()
    db.refresh(mision)
    return mision

@app.post("/personajes/{personaje_id}/misiones/{mision_id}")
def aceptar_mision(personaje_id: int, mision_id: int, db: Session = Depends(get_db)):
    personaje = db.query(Personaje).get(personaje_id)
    if not personaje:
        raise HTTPException(status_code=404, detail="Personaje no encontrado")

    orden_max = db.query(MisionPersonaje)\
        .filter_by(personaje_id=personaje_id)\
        .order_by(MisionPersonaje.orden.desc())\
        .first()
    orden = (orden_max.orden + 1) if orden_max else 1

    mp = MisionPersonaje(personaje_id=personaje_id, mision_id=mision_id, orden=orden)
    db.add(mp)
    db.commit()
    return {"mensaje": "Mision aceptada", "orden": orden}

@app.post("/personajes/{personaje_id}/completar")
def completar_mision(personaje_id: int, db: Session = Depends(get_db)):
    mp = db.query(MisionPersonaje)\
        .filter_by(personaje_id=personaje_id)\
        .order_by(MisionPersonaje.orden.asc())\
        .first()

    if not mp:
        
        raise HTTPException(status_code=404, detail="No hay misiones pendientes")

    personaje = db.query(Personaje).get(personaje_id)
    mision = db.query(Mision).get(mp.mision_id)

    personaje.experiencia += mision.experiencia
    mision.estado = 'completada'

    db.delete(mp)
    db.commit()
    return {
        "mensaje": "Mision completada",
        "xp_ganada": mision.experiencia,
        "experiencia_total": personaje.experiencia
    }

@app.get("/personajes/{personaje_id}/misiones")
def listar_misiones(personaje_id: int, db: Session = Depends(get_db)):
    misiones = db.query(MisionPersonaje)\
        .filter_by(personaje_id=personaje_id)\
        .order_by(MisionPersonaje.orden.asc())\
        .all()

    resultado = []
    for mp in misiones:
        mision = db.query(Mision).get(mp.mision_id)
        resultado.append({
            "id": mision.id,
            "nombre": mision.nombre,
            "descripcion": mision.descripcion,
            "xp": mision.experiencia,
            "estado": mision.estado,
            "orden": mp.orden
        })
    return resultado
