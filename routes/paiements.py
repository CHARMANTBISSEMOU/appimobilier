from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import requests
import uuid
import sys
sys.path.append('..')

from database import get_db, Transaction
from campay_config import CAMPAY_ACCESS_TOKEN, CAMPAY_BASE_URL

router = APIRouter(prefix="/paiements", tags=["Paiements"])


# ============================================
# MODÈLE DE DONNÉES
# ============================================
class PaiementRequest(BaseModel):
    montant: int          # Max 25 XAF en sandbox
    telephone: str        # Numéro de test Campay
    description: str      # Ex: "Publication bien"
    type_transaction: str # publication, guide, commission
    id_bien: str = "bien_test"
    id_utilisateur: str = "user_test"


# ============================================
# ROUTE : Initier un paiement
# ============================================
@router.post("/initier")
async def initier_paiement(
    paiement: PaiementRequest,
    db: Session = Depends(get_db)
):
    """
    Initier un paiement Mobile Money
    
    Pour tester utilisez ces numéros :
    - 237677777777 (MTN succès)
    - 237677777770 (MTN échec)
    - 237699999999 (Orange succès)
    - 237699999990 (Orange échec)
    
    Montant max en sandbox : 25 XAF
    """
    try:
        print(f"💰 Initiation paiement: {paiement.montant} XAF")
        
        # Générer référence unique
        reference = str(uuid.uuid4())[:16]
        
        # Appeler Campay
        headers = {
            "Authorization": f"Token {CAMPAY_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "amount": paiement.montant,
            "from": paiement.telephone,
            "description": paiement.description,
            "externalReference": reference
        }
        
        print(f"📤 Envoi vers Campay...")
        response = requests.post(
            f"{CAMPAY_BASE_URL}/collect/",
            headers=headers,
            json=data
        )
        
        campay_result = response.json()
        print(f"📥 Réponse Campay: {campay_result}")
        
        # Sauvegarder en BDD
        print("💾 Sauvegarde en BDD...")
        new_transaction = Transaction(
            id_transaction=str(uuid.uuid4()),
            id_utilisateur=paiement.id_utilisateur,
            id_bien=paiement.id_bien,
            montant=paiement.montant,
            type_transaction=paiement.type_transaction,
            reference_campay=campay_result.get("reference", reference),
            statut="en_attente",
            description=paiement.description
        )
        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)
        
        print(f"✅ Transaction sauvegardée !\n")
        
        return {
            "success": True,
            "message": "Paiement initié avec succès",
            "data": {
                "id_transaction": new_transaction.id_transaction,
                "reference_campay": new_transaction.reference_campay,
                "statut": "en_attente",
                "montant": paiement.montant,
                "telephone": paiement.telephone
            }
        }
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ROUTE : Vérifier statut paiement
# ============================================
@router.get("/verifier/{reference}")
async def verifier_paiement(reference: str):
    """
    Vérifier le statut d'un paiement avec la référence Campay
    """
    try:
        headers = {
            "Authorization": f"Token {CAMPAY_ACCESS_TOKEN}",
        }
        
        print(f"🔍 Vérification: {reference}")
        response = requests.get(
            f"{CAMPAY_BASE_URL}/transaction/{reference}/",
            headers=headers
        )
        
        result = response.json()
        print(f"📥 Statut: {result}")
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))