from fastapi import FastAPI, Header
from typing import Optional
from pydantic import BaseModel

app = FastAPI()
users = []


# the @app decorator maps .get -> HTTP GET
@app.get('/')
# API route handler fnc
async def read_root():
    return {"message": "Hello World!"}

## path param
#@app.get('/greet/{username}')
## greet route handler fnc
#async def greet(username:str):
#    return {"message":f"Hello {username}"}

#Optional params supplantin the path param ONLY, not the query param
@app.get('/greet/')
# great route handler fnc
async def greet(username:Optional[str]="User"):
    return {"message":f"Hello {username}"}

# query params have to be kept in a DS
user_list = ["Jerry", 
             "Joey",
             "Jona"]
# if a param is passed to a route handler but not explicitly (as a path param)
# it is automatically considered as a query param
@app.get('/search')
# route handler example for params that are not path params
async def search_for_user(username:str):
    for u in user_list:
        if username in user_list:
            return {"message": f"User details for user name {username}"}
        else:
            return {"message": "User not found"}    


# inheritance of BaseModel class
class UserSchema(BaseModel):
    username:str
    email:str


@app.post("/create_user")
# route to handle a /create_user POST req
async def create_user(user_data:UserSchema):
    new_user = {
        "username": user_data.username,
        "user_data": user_data.email
    }

    users.append(new_user)    
    return{"message":"User created successfully", "user":new_user}

# req hdrs getter
@app.get("/get_headers")
# route path
async def get_all_req_hdrs(
    # app, os, version
    user_agent: Optional[str] = Header(None),
    # server domain name, tcp port
    host: Optional[str] = Header(None),
    # tell server which data types can be sent back
    accept: Optional[str] = Header(None),
    # preferred human language on which data types can be sent back
    accept_language: Optional[str] = Header(None),
    # compression algo
    accept_encoding: Optional[str] = Header(None),
    # referer from prev page
    referer: Optional[str] = Header(None),
    # does the connection stay open after the current transaction finishes
    connection: Optional[str]=Header(None)
): 
    request_headers={}
    # app, os, version
    request_headers["User-Agent"]=user_agent
    # server domain name, tcp port
    request_headers["Host"]=host
    # tell server which data types can be sent back
    request_headers["Accept"]=accept
    # preferred human language on which data types can be sent back
    request_headers["Accept-Language"]=accept_language
    # compression algo
    request_headers["Accept-Encoding"]=accept_encoding
    # referer from prev page
    request_headers["Referer"] = referer
    # does the connection stay open after the current transaction finishes
    request_headers["Connection"]=connection
    return request_headers

