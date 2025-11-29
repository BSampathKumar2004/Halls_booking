from pydantic import BaseModel, EmailStr

class AdminBase(BaseModel):
    name: str
    email: EmailStr

    class Config:
        from_attributes = True


class AdminCreate(AdminBase):
    password: str


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class AdminOut(AdminBase):
    id: int
