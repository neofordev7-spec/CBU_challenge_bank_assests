from pydantic import BaseModel


class CategoryBase(BaseModel):
    name: str
    code: str
    description: str | None = None
    useful_life_months: int | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    useful_life_months: int | None = None
    is_active: bool | None = None


class CategoryResponse(CategoryBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
