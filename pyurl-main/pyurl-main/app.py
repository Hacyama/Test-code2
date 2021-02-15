from pymongo import MongoClient

client = MongoClient('mongodb://localhost:14701/')

db = client.main

def db_write_url(origin_url, shorten_url, collection = db.collection):
    post = {"origin_url": origin_url,
            "shorten_url": shorten_url}
    posts = db.collection
    post_id = posts.insert_one(post).inserted_id
    return post_id

def db_read_by_shorten_url(shorten_url, collection = db.collection):
    return collection.find_one({"shorten_url": shorten_url})

def getAlreadyHave(origin_url, collection = db.collection):
    return collection.find_one({"origin_url": origin_url})

import random
import string

def get_random_string(length):
    letters = string.ascii_lowercase + string.ascii_uppercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


# uvicorn filename:app --port 8001 --workers 5 --proxy-headers

from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, HTTPException, Query, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
import uvicorn
import time

import re
import requests

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from pydantic import BaseModel
from typing import Optional

class shorten_url_data(BaseModel):
    url: str
    except_link: Optional[str] = None

@app.post("/api/post/shorten_url/")
async def shorten_url(data: shorten_url_data):
    
    origin_url = data.url
    
    try:
        requests.get(origin_url)
    except:
        return {"message": "fail, please enter a valid url.",
                "shorten_url": None,
                "origin_url": origin_url}
    
    already_have = getAlreadyHave(origin_url)
    if already_have:
        shorten_url = already_have["shorten_url"]
        return {"message": "success, already have one.",
                "shorten_url": f"https://pyurl.cc/{shorten_url}",
                "origin_url": origin_url}
    else:
        for i in range(10):
            url_len = int((7+i)/2)
            shorten_url = get_random_string(url_len)
            print(shorten_url)
            if db_read_by_shorten_url(shorten_url):
                #already have one
                continue
            else:
                result = db_write_url(origin_url, shorten_url)
                return {"message": "success",
                        "shorten_url": f"https://pyurl.cc/{shorten_url}",
                        "origin_url": origin_url}
        return {"message": "fail to save url.",
                "shorten_url": None,
                "origin_url": None}


pattern = r"\b(TelegramBot|TwitterBot|PlurkBot|facebookexternalhit|ZXing|okhttp|jptt|Mo PTT|curl|Wget)\b"

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

@app.get("/{shorten_url}", response_class=HTMLResponse)
async def get_url(request: Request, shorten_url):
    if shorten_url == "":
        return {"message": "Home page is still building..."}
    
    redirect_url = db_read_by_shorten_url(shorten_url)["origin_url"]
    
    if redirect_url:
        if re.search(pattern, request.headers["user-agent"]): #如果是機器人來抓網頁資訊
            return requests.get(redirect_url).text

        return templates.TemplateResponse("redir.html", {"request": request, "url": redirect_url})



@app.get("/qrcode/")
async def returnQrcode(request: Request, url: str ="Hi"):#token: str = Depends(oauth2_scheme)):
    print("URL", url)
    url = url.replace(" ", "+")
    return templates.TemplateResponse("qrCode.html", {"request": request, "link": url})


if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=11133)