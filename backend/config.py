import os

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "RailPredict AI")
    MODEL_PATH: str = os.getenv("MODEL_PATH", "ml/models/eta_xgboost_pipeline.pkl")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # PostgreSQL Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:password123@localhost:5432/railpredict_prototype"
    )

settings = Settings()
