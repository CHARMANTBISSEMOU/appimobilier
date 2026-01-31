from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
import sys
sys.path.append('..')

from utils.image_handler import compress_image, upload_image_to_cloudinary, delete_image_from_cloudinary
from config import IMAGE_MAX_SIZE, IMAGE_QUALITY, MAX_IMAGES_PER_BIEN
from database import get_db, Image
import cloudinary.uploader
import uuid

# Créer le router
router = APIRouter(prefix="/images", tags=["Images"])


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    id_bien: str = None,
    db: Session = Depends(get_db)
):
    """
    Upload UNE photo et sauvegarde en BDD
    
    Paramètres:
    - file: Le fichier image
    - id_bien: ID du bien (optionnel pour test)
    """
    # Vérifier format
    allowed_formats = ['image/jpeg', 'image/png', 'image/webp']
    if file.content_type not in allowed_formats:
        raise HTTPException(status_code=400, detail="Format non supporté")
    
    try:
        print(f"📥 Réception de: {file.filename}")
        image_data = await file.read()
        
        # Vérifier taille max 10 MB
        if len(image_data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image trop grosse (max 10 MB)")
        
        # Compresser
        print("🗜️ Compression...")
        compressed_data = compress_image(image_data, IMAGE_MAX_SIZE, IMAGE_QUALITY)
        
        # Upload Cloudinary
        print("☁️ Upload sur Cloudinary...")
        result = upload_image_to_cloudinary(compressed_data)
        
        # Sauvegarder en BDD
        print("💾 Sauvegarde en base de données...")
        new_image = Image(
            id_image=str(uuid.uuid4()),
            id_bien=id_bien or "bien_test",  # Si pas d'id_bien, on met "bien_test"
            url_cloudinary=result['url']
        )
        db.add(new_image)
        db.commit()
        db.refresh(new_image)
        
        print(f"✅ Image uploadée et sauvegardée !\n")
        
        return {
            "success": True,
            "message": "Image uploadée avec succès",
            "data": {
                "id_image": new_image.id_image,
                "id_bien": new_image.id_bien,
                "url": result['url'],
                "public_id": result['public_id'],
                "date_upload": new_image.date_upload.isoformat()
            }
        }
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/videos/upload")
async def upload_video(
    file: UploadFile = File(...),
    id_bien: str = None,
    db: Session = Depends(get_db)
):
    """Upload UNE vidéo (max 1 min, max 50 MB) et sauvegarde en BDD"""
    allowed_formats = ['video/mp4', 'video/quicktime', 'video/x-msvideo']
    if file.content_type not in allowed_formats:
        raise HTTPException(status_code=400, detail="Format vidéo non supporté")
    
    try:
        print(f"🎥 Réception de: {file.filename}")
        video_data = await file.read()
        
        # Vérifier taille max 50 MB
        size_mb = len(video_data) / (1024 * 1024)
        if size_mb > 50:
            raise HTTPException(status_code=400, detail=f"Vidéo trop grosse ({size_mb:.1f} MB)")
        
        print(f"   Taille: {size_mb:.1f} MB")
        
        # Upload Cloudinary
        print("☁️ Upload vidéo sur Cloudinary...")
        result = cloudinary.uploader.upload(
            video_data,
            resource_type="video",
            folder="videos"
        )
        
        # Sauvegarder en BDD
        print("💾 Sauvegarde en base de données...")
        new_video = Image(  # On utilise la même table "image"
            id_image=str(uuid.uuid4()),
            id_bien=id_bien or "bien_test",
            url_cloudinary=result['secure_url']
        )
        db.add(new_video)
        db.commit()
        db.refresh(new_video)
        
        print(f"✅ Vidéo uploadée et sauvegardée !\n")
        
        return {
            "success": True,
            "message": "Vidéo uploadée avec succès",
            "data": {
                "id_image": new_video.id_image,
                "id_bien": new_video.id_bien,
                "url": result['secure_url'],
                "public_id": result['public_id'],
                "taille_mb": round(size_mb, 2),
                "date_upload": new_video.date_upload.isoformat()
            }
        }
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bien/{id_bien}")
async def get_images_by_bien(id_bien: str, db: Session = Depends(get_db)):
    """
    Récupérer toutes les images d'un bien
    """
    images = db.query(Image).filter(Image.id_bien == id_bien).all()
    
    if not images:
        raise HTTPException(status_code=404, detail="Aucune image trouvée pour ce bien")
    
    return {
        "success": True,
        "count": len(images),
        "data": [
            {
                "id_image": img.id_image,
                "url": img.url_cloudinary,
                "date_upload": img.date_upload.isoformat()
            }
            for img in images
        ]
    }


@router.delete("/delete/{public_id:path}")
async def delete_image(public_id: str):
    """Supprimer une image de Cloudinary"""
    try:
        result = delete_image_from_cloudinary(public_id)
        
        if result.get('result') == 'ok':
            return {
                "success": True,
                "message": "Image supprimée avec succès"
            }
        else:
            raise HTTPException(status_code=404, detail="Image non trouvée")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")