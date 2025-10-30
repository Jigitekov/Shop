from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Numeric, func
from sqlalchemy.orm import sessionmaker, declarative_base, Session


DATABASE_URL = "postgresql+psycopg://postgres:3374@127.0.0.1:5432/website"


engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    address = Column(String(255), nullable=True)
    phone_number = Column(String(30), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(120), nullable=False, index=True)
    description = Column(String(1000), nullable=True)
    price = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Shop API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    address: Optional[str] = None
    phone_number: Optional[str] = None

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  
    id: int
    username: str
    email: EmailStr
    address: Optional[str] = None
    phone_number: Optional[str] = None

class ProductCreate(BaseModel):
    product_name: str
    description: Optional[str] = None
    price: float

class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_name: str
    description: Optional[str] = None
    price: float


@app.post("/users", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=payload.password,  
        address=payload.address,
        phone_number=payload.phone_number,
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Cannot create user: {e}")

@app.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@app.get("/users/{user_id}", response_model=UserOut)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/products", response_model=ProductOut)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = Product(
        product_name=payload.product_name,
        description=payload.description,
        price=payload.price,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@app.get("/products", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
