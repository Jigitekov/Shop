from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

# Define the connection string to your MSSQL database
DATABASE_URL = "mssql+pyodbc://@localhost\\SQLEXPRESS/project.rz?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"

app = FastAPI()

# Create an engine that the Session will use for connection resources
engine = create_engine(DATABASE_URL)

# Reflect an existing database into a new model
Base = automap_base()
# Reflect the tables
Base.prepare(engine, reflect=True)

# mapped classes are now created with names by default
# matching that of the table name.
User = Base.classes.Users  # Make sure this matches the table name exactly
Product = Base.classes.Products

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserCreate(BaseModel):
    username: str
    email: str
    address: str
    phone_number: str
    user_id: int
    password: str

class UserCheck(BaseModel):
    user_id: int
    password: str

@app.get("/users/")
def read_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    # Serialize the query results into a JSON-compatible format
    return [
        {
            "username": user.username,
            "email": user.email,
            "user_id": user.user_id,
            "address": user.address,
            "phone_number": user.phone_number,
        }
        for user in users
    ]

@app.get("/products/")
def read_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    # Serialize the query results into a JSON-compatible format
    return [
        {
            "product_name": product.product_name,
            "description": product.description,
            "product_ID": product.product_ID,
            "price": product.price,
        }
        for product in products
    ]



@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Logic to create a new user in the database
    db_user = User(username=user.username, email=user.email, address=user.address, phone_number=user.phone_number, user_id=user.user_id,password=user.password)
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error creating user")

@app.post("/userCheck/")
def check_user(user: UserCheck, db: Session = Depends(get_db)):
    # Logic to create a new user in the database
    existing_user = db.query(User).filter(User.user_id == user.user_id).first()

    if existing_user:
        print("Yes")
    else:
        print("NO")
    return{"message": {"User checked"}}
if __name__ == "__main__":
    import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)