from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

class RGPDMiddleware(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        # Vérification des droits d'accès
        if not self.verify_rgpd_access(credentials.credentials):
            raise HTTPException(
                status_code=403,
                detail="Accès non autorisé aux données personnelles"
            )
        
        # Audit de l'accès
        self.log_access(request, credentials.credentials)
        
        return credentials.credentials
    
    def verify_rgpd_access(self, token: str) -> bool:
        """Vérification que l'utilisateur a le droit d'accéder aux données"""
        try:
            payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
            return payload.get('rgpd_authorized', False)
        except:
            return False
    
    def log_access(self, request: Request, user_id: str):
        """Journalisation des accès aux données personnelles"""
        audit_log = {
            'user_id': user_id,
            'endpoint': request.url.path,
            'timestamp': datetime.now(),
            'ip_address': request.client.host
        }
        # Sauvegarde en base de données
       self.save_audit_log(audit_log)