from pydantic import BaseModel

class TenantRegister(BaseModel):
    name: str
    email: str
    password: str

class TenantResponse(BaseModel):
    name: str
    email: str
    api_key: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
