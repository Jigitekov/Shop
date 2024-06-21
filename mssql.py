from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI, Depends, HTTPException, status, Path
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import class_mapper, ColumnProperty

DATABASE_URL = "mssql+pyodbc://@localhost\SQLEXPRESS/WebSite?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes&TrustServerCertificate=yes"
#DATABASE_URL = "mssql+pyodbc://@localhost\\SQLEXPRESS/WebSite?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
app = FastAPI()

engine = create_engine(DATABASE_URL)

Base = automap_base()
Base.prepare(engine, reflect=True)

User = Base.classes.Users  
Product = Base.classes.Products

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class UserCreate(BaseModel):
    username: str
    usersurname: str
    email: EmailStr
    address: str
    password: str
    
class ProductCreate(BaseModel):
    ProductID: int
    ProductName: str
    Description: str
    Price: int

class UserLogin(BaseModel):
    email: EmailStr
    password: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/users/")
def User_List(db: Session = Depends(get_db)):
    try:
        users = db.query(User).all()
        return [
            {
                "username": user.UserName,  
                "email": user.Email,        
                "user_id": user.UserID,     
                "address": user.Address     
            }
            for user in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/")
def Product_List(db: Session = Depends(get_db)):
    try:
        products = db.query(Product).all()
        return [
            {
                "product_name": product.ProductName,
                "description": product.Description,
                "product_ID": product.ProductID,
                "price": product.Price,
            }
            for product in products
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users/")
def Registration(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.Email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = pwd_context.hash(user.password)
    
    db_user = User(
        UserName=user.username, 
        UserSurname=user.usersurname,
        Email=user.email, 
        Address=user.address,
        Password=hashed_password
    )
    
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
        return {
            "UserName": db_user.UserName,
            "UserSurname": db_user.UserSurname,
            "Email": db_user.Email,
            "Address": db_user.Address
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/login/")
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.Email == user_credentials.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if not pwd_context.verify(user_credentials.password, user.Password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    
    return {"message": "Login successful", "user_id": user.UserID}


@app.post("/products/", response_model=ProductCreate, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    existing_product = db.query(Product).filter(Product.ProductID == product.ProductID).first()
    if existing_product:
        raise HTTPException(status_code=400, detail="Product with this ProductID already exists")
    
    new_product = Product(
        ProductID=product.ProductID,
        ProductName=product.ProductName,
        Description=product.Description,
        Price=product.Price
    )
    
    db.add(new_product)
    try:
        db.commit()
        db.refresh(new_product)
        return new_product
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
######DELETE
@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int = Path(..., title="The ID of the user to delete"), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.UserID == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    db.delete(user)
    try:
        db.commit()
        return {"message": "User deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.delete("/ptoduct/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int = Path(..., title="The ID of the user to delete"), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.ProductID == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    db.delete(product)
    try:
        db.commit()
        return {"message": "Product deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

if __name__ == "__main__":
    import uvicorn
uvicorn.run(app, host="127.0.0.1", port=8000)