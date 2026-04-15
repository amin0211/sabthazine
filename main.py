# flet clean
# flet build apk 

import flet as ft
import requests
import urllib.request
import hashlib
#import bcrypt
import json
import os
from dotenv import load_dotenv

# from SabteHazine import sabte_hazine_view
#from Hazineha import hazinaha_view
SUPABASE_URL = "https://gisyttrgmhbuxvmsjdfm.supabase.co"

load_dotenv()
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ================= SUPABASE CONFIG =================

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ================= PASSWORD =================
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password, hashed):
    return hashlib.sha256(password.encode()).hexdigest() == hashed

# ================= SUPABASE REST =================
def get_user(username):
    url = f"{SUPABASE_URL}/rest/v1/users?username=eq.{username}"

    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req) as response:
        data = response.read()
        return json.loads(data)
    

def register_user(data):
    url = f"{SUPABASE_URL}/rest/v1/users"
    return requests.post(url, headers=headers, json=data)

# ================= LOGIN =================
def login_view(page: ft.Page):

    username = ft.TextField(label="Username")
    password = ft.TextField(label="Password", password=True)

    def login(e):

        try:
            users = get_user(username.value)

            if users:

                user = users[0]
                with open("user.json", "w") as f:
                    json.dump(user, f)
                page.go("/sabtehazine")
                # if check_password(password.value, user["password_hash"]):
                #     with open("user.json", "w") as f:
                #         json.dump(user, f)
                #     page.go("/sabtehazine")

                # else:
                #     page.snack_bar = ft.SnackBar(ft.Text("Wrong password"))
                #     page.snack_bar.open = True
                #     page.update()

            else:
                page.snack_bar = ft.SnackBar(ft.Text("User not found"))
                page.snack_bar.open = True
                page.update()

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"))
            page.snack_bar.open = True
            page.update()

    return ft.View(
        route="/login",
        controls=[
            ft.Text("Login", size=25),
            username,
            password,
            ft.Button("Login", on_click=login),
            ft.TextButton("Register", on_click=lambda e: page.go("/register"))
        ]
    )

# ================= REGISTER =================
def register_view(page: ft.Page):

    username = ft.TextField(label="Username")
    name = ft.TextField(label="Name")
    family = ft.TextField(label="Family")
    birthdate = ft.TextField(label="Birthdate (YYYY-MM-DD)")
    password = ft.TextField(label="Password", password=True)

    def register(e):

        try:
            hashed = hash_password(password.value)

            register_user({
                "username": username.value,
                "password_hash": hashed,
                "name": name.value,
                "family": family.value,
                "birthdate": birthdate.value
            })

            page.go("/login")

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"))
            page.snack_bar.open = True
            page.update()

    return ft.View(
        route="/register",
        controls=[
            ft.Text("Register", size=25),
            username,
            name,
            family,
            birthdate,
            password,
            ft.Button("Create Account", on_click=register),
            ft.TextButton("Back", on_click=lambda e: page.go("/login"))
        ]
    )

# ================= MAIN =================
def main_view(page: ft.Page):

    user = page.data.get("user") if page.data else None

    def logout(e):
        try:
            page.client_storage.remove("user")
        except:
            pass
        page.go("/login")

    return ft.View(
        route="/main",
        controls=[
            ft.Text("Main Page", size=25),
            ft.Button("Logout", on_click=logout)
        ]
    )

# ================= ROUTING =================
def main(page: ft.Page):

    start_picker = ft.DatePicker()
    end_picker = ft.DatePicker()
    page.overlay.extend([start_picker, end_picker])

    def route_change(e):

        page.views.clear()

        if page.route == "/login":
            page.views.append(login_view(page))

        elif page.route == "/register":
            page.views.append(register_view(page))

        elif page.route == "/main":
            page.views.append(main_view(page))

        # elif page.route == "/sabtehazine":
        #     page.views.append(sabte_hazine_view(page, start_picker, end_picker))

        # elif page.route == "/hazinaha_view":
        #     page.views.append(hazinaha_view(page))

        else:
            page.views.append(ft.View("/", [ft.Text("404 Page")]))

        page.update()

    page.on_route_change = route_change

    page.go("/login")

# ================= RUN =================
ft.app(target=main)