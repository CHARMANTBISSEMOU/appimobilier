from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

# URL de connexion Clever Cloud
DATABASE_URL = "mysql+pymysql://ubqfrg1jt1rcrrbd:lwsrLlQHZ2N4GBZrRyp4@ba6oqh14fw458rq0atuj-mysql.services.clever-cloud.com:3306/ba6oqh14fw458rq0atuj"

# Créer l'engine
engine = create_engine(DATABASE_URL, echo=True)

# Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()

# ============================================
# MODÈLE IMAGE
# ============================================
class Image(Base):
    __tablename__ = "image"
    
    id_image = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_bien = Column(String(255), nullable=False)
    url_cloudinary = Column(String(500), nullable=False)
    date_upload = Column(DateTime, default=datetime.now)

class Transaction(Base):
    __tablename__ = "transaction"
    
    id_transaction = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_utilisateur = Column(String(255), nullable=False)
    id_bien = Column(String(255), nullable=False)
    montant = Column(Integer, nullable=False)
    type_transaction = Column(String(50), nullable=False)
    reference_campay = Column(String(100), nullable=False)
    statut = Column(String(20), default="en_attente")
    description = Column(String(500))
    date_transaction = Column(DateTime, default=datetime.now)
# ============================================
# FONCTION : Obtenir une session BDD
# ============================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()