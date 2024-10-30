from fastapi import FastAPI, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import pyodbc
import bcrypt
import uvicorn
from pydantic import BaseModel
from starlette.requests import Request

app = FastAPI()

# Database configuration
server = 'LAPTOP-PAEKKFI8\\SQLEXPRESS'
username = 'Suryakanta_2003'
password = '123456789'
database = 'GOVERMENT'

# Connection string for SQL Server
connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};UID={username};PWD={password};DATABASE={database}'

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Jinja2 templates
templates = Jinja2Templates(directory="C:\\Users\\HP\\Desktop\\fastapi_project1\\demoproject\\templets")

# Password hashing functions
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def check_password(stored_password, provided_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

# Create the users table if it doesn't exist
def create_table_if_not_exists():
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        create_table_query = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
        CREATE TABLE Users (
            UserID INT PRIMARY KEY IDENTITY(1,1),
            Name NVARCHAR(100),
            Email NVARCHAR(100) UNIQUE,
            MobileNo NVARCHAR(15),
            Organization NVARCHAR(100),
            Username NVARCHAR(50) UNIQUE,
            Password NVARCHAR(100),
            Remark NVARCHAR(255)
        )
        """
        cursor.execute(create_table_query)
        conn.commit()
    except pyodbc.Error as e:
        print(f"Database error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

create_table_if_not_exists()

# Pydantic model for user data
class User(BaseModel):
    name: str
    email: str
    mobile_no: str
    organization: str
    username: str
    password: str
    remark: str

# Function to insert user into the database
def insert_user(user_data: User):
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        insert_data_query = """
        INSERT INTO Users (Name, Email, MobileNo, Organization, Username, Password, Remark) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(insert_data_query, (
            user_data.name,
            user_data.email,
            user_data.mobile_no,
            user_data.organization,
            user_data.username,
            user_data.password,  # Store the hashed password here
            user_data.remark
        ))
        conn.commit()
        return True
    except pyodbc.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

# Function to validate user credentials
def validate_user(username, password):
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        query = "SELECT * FROM Users WHERE (Email = ? OR Username = ?)"
        cursor.execute(query, (username, username))
        user = cursor.fetchone()
        if user and check_password(user.Password, password):
            return True
        else:
            return False
    except pyodbc.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

# Root endpoint to serve HTML
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Signup endpoint
@app.post("/signup")
async def signup(
    name: str = Form(...),
    email: str = Form(...),
    mobile_no: str = Form(...),
    organization: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    remark: str = Form(...),
):
    hashed_password = hash_password(password)
    user_data = User(
        name=name,
        email=email,
        mobile_no=mobile_no,
        organization=organization,
        username=username,
        password=hashed_password,
        remark=remark
    )
    if insert_user(user_data):
        return {"message": "Signup successful!"}
    else:
        raise HTTPException(status_code=400, detail="User registration failed.")

# Login endpoint
@app.post("/login")
async def login(
    username_email: str = Form(...),
    password: str = Form(...),
):
    if validate_user(username_email, password):
        return {"message": "Login successful!"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials.")

# Initialize the database
create_table_if_not_exists()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
