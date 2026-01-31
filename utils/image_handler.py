from PIL import Image
import cloudinary.uploader
import io
import os

def compress_image(image_file, max_size=(1200, 1200), quality=75):
    """Compresse une image"""
    # Si c'est un chemin
    if isinstance(image_file, str):
        img = Image.open(image_file)
        original_size = os.path.getsize(image_file)
    # Si c'est des bytes
    else:
        img = Image.open(io.BytesIO(image_file))
        original_size = len(image_file)
    
    # Convertir en RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Redimensionner
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Compresser
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=quality, optimize=True)
    compressed_data = buffer.getvalue()
    
    print(f"📊 Compression: {original_size:,} → {len(compressed_data):,} bytes")
    
    return compressed_data


def upload_image_to_cloudinary(image_data, folder="biens"):
    """Upload sur Cloudinary"""
    result = cloudinary.uploader.upload(
        image_data,
        folder=folder,
        resource_type="image"
    )
    
    return {
        "url": result['secure_url'],
        "public_id": result['public_id'],
        "bytes": result['bytes']
    }


def delete_image_from_cloudinary(public_id):
    """Supprimer de Cloudinary"""
    result = cloudinary.uploader.destroy(public_id)
    return result