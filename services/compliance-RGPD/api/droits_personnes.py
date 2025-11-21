# api/droits_personnes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import smtplib
from email.mime.text import MimeText

router = APIRouter()

class DroitAccesRequest(BaseModel):
    nom: str
    email: str
    identifiant_annonce: str = None
    type_demande: str  # acces, rectification, suppression

@router.post("/exercer-droits")
async def exercer_droits_rgpd(request: DroitAccesRequest):
    """
    Endpoint pour l'exercice des droits RGPD
    """
    
    # Validation de la demande
    if not self.validate_demande(request):
        raise HTTPException(status_code=400, detail="Demande invalide")
    
    # Traitement selon le type de demande
    if request.type_demande == "acces":
        return await traiter_droit_acces(request)
    elif request.type_demande == "rectification":
        return await traiter_droit_rectification(request)
    elif request.type_demande == "suppression":
        return await traiter_droit_suppression(request)
    
    raise HTTPException(status_code=400, detail="Type de demande non supporté")

async def traiter_droit_suppression(request: DroitAccesRequest):
    """Traitement du droit à l'effacement"""
    # Recherche et suppression des données personnelles
    suppression_count = await supprimer_donnees_personnelles(request)
    
    # Confirmation au demandeur
    await envoyer_confirmation_suppression(request, suppression_count)
    
    return {
        "status": "success",
        "message": f"Suppression de {suppression_count} enregistrements effectuée",
        "delai": "15 jours maximum"
    }