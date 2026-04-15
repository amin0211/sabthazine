
import flet as ft
#from openai import OpenAI
import json, re
import os
from datetime import datetime, timedelta, date
import speech_recognition as sr
import asyncio
import threading
import urllib.request
import urllib.parse
from dotenv import load_dotenv

# ---------------- OPENAI ----------------
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------- SUPABASE REST ----------------

SUPABASE_URL = "https://gisyttrgmhbuxvmsjdfm.supabase.co"

load_dotenv()
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# ---------------- HTTP HELPERS ----------------
def safe_request(req):
    try:
        with urllib.request.urlopen(req) as res:
            raw = res.read()

            if not raw:
                return None

            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")

            try:
                return json.loads(raw)
            except:
                return raw

    except Exception as e:
        print("HTTP ERROR:", e)
        return None
    
def supa_get(table, query=""):
    url = f"{SUPABASE_URL}/rest/v1/{table}?{query}"
    req = urllib.request.Request(url, headers=HEADERS)
    return safe_request(req)

def supa_post(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers=HEADERS,
        method="POST"
    )

    try:
        return safe_request(req)     
        # with urllib.request.urlopen(req) as res:
        #     raw = res.read().decode()

        #     if not raw:
        #         return data  # fallback

        #     return json.loads(raw)

    except Exception as e:
        print("POST ERROR:", e)
        return data
    

def supa_patch(table, data, match):
    query = urllib.parse.urlencode(match)
    url = f"{SUPABASE_URL}/rest/v1/{table}?{query}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers=HEADERS,
        method="PATCH"
    )
    req.get_method = lambda: "PATCH"
    return safe_request(req)

def supa_delete(table, match):
    query = urllib.parse.urlencode(match)
    url = f"{SUPABASE_URL}/rest/v1/{table}?{query}"
    req = urllib.request.Request(url, headers=HEADERS, method="DELETE")
    safe_request(req)

# def parse_expense_with_openai(text):
#     try:
#         response = client.chat.completions.create(
#             model="gpt-5-mini",
#             messages=[
#             {
#             "role": "system",
#             "content": """
#             Return ONLY valid JSON.

#             Rules:
#             - Keys: hazine, price, currency, date
#             - date must be YYYY-MM-DD

#             IMPORTANT:
#             - NEVER calculate or guess dates
#             - ONLY extract date if explicitly written in the text
#             - If no exact date is written, set date = null

#             Return format:
#             {
#             "hazine": "...",
#             "price": 0,
#             "currency": "CAD",
#             "date": null
#             }
#             """
#             },
#                 {"role": "user", "content": text}
#             ]
#         )

#         raw = response.choices[0].message.content

#         if not raw:
#             return {}

#         match = re.search(r"\{.*\}", raw, re.DOTALL)
#         if not match:
#             return {}

#         return json.loads(match.group(0))

#     except:
#         return {}
    
def parse_expense_with_openai(text):
    try:
        url = "https://sabthazine.onrender.com/parse"

        data = json.dumps({"text": text}).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=10) as res:
            raw = res.read().decode("utf-8")

        return json.loads(raw)

    except Exception as e:
        print("API ERROR:", e)
        return {}
        
def normalize_date(date_value, text):
    text = text.lower()

    if "yesterday" in text or "دیروز" in text:
        return (date.today() - timedelta(days=1)).isoformat()

    if "today" in text or "امروز" in text:
        return date.today().isoformat()

    # اگر AI چیزی گفت ولی خالی بود → امروز
    if not date_value:
        return date.today().isoformat()

    return date_value
    
# ---------------- VIEW ----------------
def sabte_hazine_view(page, start_picker, end_picker):

    chat_column = ft.Column(expand=True, scroll=ft.ScrollMode.ALWAYS)
    input_field = ft.TextField(hint_text="هزینه را بنویس...", expand=True)


    start_date = date.today()
    end_date = date.today()

    # ---------------- LOAD ----------------
    def load_messages():
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()
        
        query = (
            f"select=*&date_cost=gte.{start_str}&date_cost=lte.{end_str}&order=id.desc"
        )
        print(f"555666 = {query}")

        res = supa_get("cost", query)
        print(f"666 = {res}")
        chat_column.controls.clear()
        for row in res:
            chat_column.controls.append(create_message(row))

        print(f"777 = {res}")

        page.update()

    def get_hazine_id(hazine):
        query = f"select=id&title=eq.{urllib.parse.quote(hazine)}"
        res = supa_get("hazineha", query)

        if res and len(res) > 0:
            return res[0]["id"]

        return None
    
    def get_currency_id(currency_type):
        query = f"select=id&currency_type=eq.{urllib.parse.quote(currency_type)}"
        res = supa_get("currency", query)

        if res and len(res) > 0:
            return res[0]["id"]

        return None    
    
    # ---------------- SAVE ----------------
    def save_cost(title, price, hazine, currency, date_cost, cost_id=None):
        hazine_id = get_hazine_id(hazine)
        currency_id = get_currency_id(currency)

        data = {
            "title": title,
            "price": price,
            "currency_id": currency_id,
            "id_hazine": hazine_id,
            "date_cost": date_cost
        }

        if cost_id:
            supa_patch("cost", data, {"id": cost_id})
            return {**data, "id": cost_id}
        else:
            res = supa_post("cost", data)

        if isinstance(res, list) and len(res) > 0:
            return res[0]

        return {**data, "id": "temp"}
        
        

    # ---------------- DELETE ----------------
    def delete_cost(cost_id):
        supa_delete("cost", {"id": cost_id})

    # ---------------- MESSAGE UI ----------------
    def create_message(row):

        def delete_message(e):
            delete_cost(row["id"])
            chat_column.controls.remove(container)
            page.update()

        def edit_message(e):
            input_field.value = row["title"]
            input_field.data = row["id"]
            page.update()

        container = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(row["title"]),
                    ft.Text(row.get("date_cost", ""), size=10, color="grey")
                ]),
                ft.Row([
                    ft.IconButton(ft.Icons.EDIT, on_click=edit_message),
                    ft.IconButton(ft.Icons.DELETE, on_click=delete_message),
                ])
            ]),
            padding=10,
            bgcolor="#DCF8C6",
            border_radius=10,
            margin=5
        )

        container.data = row["id"]
        
        return container

    # ---------------- SEND ----------------
        
    def send_message(e):
        text = input_field.value.strip()
        if not text:
            return
        
            # جلوگیری از ارسال تکراری
        if getattr(input_field, "sending", False):
            return

        input_field.sending = True

        data = parse_expense_with_openai(text)
     
        title = text
        price = data.get("price", 0)
        currency = data.get("currency", "CAD")
        hazine = data.get("hazine", "CAD")
        
        date_cost = normalize_date(
                data.get("date"),
                text
            )
        
        cost_id = getattr(input_field, "data", None)
        save_cost(title, price, hazine, currency, date_cost, cost_id)
           
        input_field.value = ""

        input_field.data = None
        
        load_messages()
        page.update()
        
        input_field.sending = False


    input_field.on_submit = send_message
    input_field.on_blur = send_message

    # ---------------- INPUT ----------------
    
    send_button = ft.ElevatedButton("ارسال", on_click=send_message)
    
    input_row = ft.Row([
        ft.IconButton(ft.Icons.MIC),
        input_field,
        send_button
    ])

    # ---------------- DATE PICKERS (همان UI خودت) ----------------
    def update_start(e):
        nonlocal start_date

        if start_picker.value is None:
            return

        start_date = start_picker.value.date()
        start_btn.content = ft.Text(start_date.isoformat())
        start_btn.update()
    
    
        load_messages()
            
    def update_end(e):
        nonlocal end_date

        if end_picker.value is None:
            return

        end_date = end_picker.value.date()
        end_btn.content = ft.Text(end_date.isoformat())
        end_btn.update()

        load_messages()
            
    start_picker = ft.DatePicker()
    end_picker = ft.DatePicker()

    start_picker.on_change = update_start
    end_picker.on_change = update_end
    
    page.overlay.append(start_picker)
    page.overlay.append(end_picker)

    def open_start(e):
        start_picker.open = True
        page.update()

    def open_end(e):
        end_picker.open = True
        page.update()
    
    
    start_btn = ft.ElevatedButton(
        content=ft.Text(start_date.isoformat()),
        on_click=open_start
    )

    end_btn = ft.ElevatedButton(
        content=ft.Text(end_date.isoformat()),
        on_click=open_end
    )

    tree_btn = ft.IconButton(
        icon=ft.Icons.ACCOUNT_TREE,
        on_click=lambda e: page.go("/hazinaha_view")
    )

    top_bar = ft.Container(
        content=ft.Row([
            ft.Row([start_btn, end_btn]),
            ft.Container(expand=True),
            tree_btn
        ]),
        padding=10,
        bgcolor="#f5f5f5"
    )

    # ---------------- INIT ----------------
    load_messages()

    return ft.View(
        route="/sabtehazine",
        controls=[
            ft.Column([
                top_bar,
                chat_column,
                input_row
            ], expand=True)
        ]
    )