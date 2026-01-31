from fastapi import APIRouter, Request, HTTPException
import sys
sys.path.append('..')

from campay_config import CAMPAY_WEBHOOK_KEY

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/campay")
async def campay_webhook(request: Request):
    """
    Campay appelle cette route automatiquement
    quand un paiement est confirmé ou échoué
    """
    try:
        # 1. Recevoir les données de Campay
        data = await request.json()
        print(f"📥 Webhook reçu: {data}")
        
        # 2. Extraire les infos
        reference = data.get("reference")
        status = data.get("status")
        montant = data.get("amount")
        telephone = data.get("phone_number")
        
        print(f"   Reference: {reference}")
        print(f"   Status: {status}")
        print(f"   Montant: {montant}")
        print(f"   Téléphone: {telephone}")
        
        # 3. Selon le statut
        if status == "SUCCESSFUL":
            print("✅ Paiement réussi !")
            
        elif status == "FAILED":
            print("❌ Paiement échoué !")
        
        # 4. Retourner 200 OK à Campay
        return {
            "success": True,
            "message": "Webhook reçu"
        }
        
    except Exception as e:
        print(f"❌ Erreur webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))