from pydantic import BaseModel

class AmenityBase(BaseModel):
    name: str

class AmenityCreate(AmenityBase):
    pass

class AmenityOut(AmenityBase):
    id: int

    model_config = {"from_attributes": True}
