import os
import requests
import gspread
from google.oauth2.service_account import Credentials
from datetime import date
import aiohttp
import asyncio
import json
import aiohttp
import asyncio
from datetime import date
from google.oauth2 import service_account
import google.auth.transport.requests
from dotenv import load_dotenv


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


load_dotenv()

SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_access_token():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    creds.refresh(google.auth.transport.requests.Request())
    return creds.token


async def update_google_sheet(value: float):
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    async with aiohttp.ClientSession(headers=headers) as session:
        url_get = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{SHEET_NAME}!A1:ZZ1000"
        async with session.get(url_get) as resp:
            data = await resp.json()

        values = data.get("values", [])
        today = date.today().strftime("%d.%m.%Y")

        while len(values) < 7:
            values.append([])

        header = values[3] if len(values) > 3 else []
        if today in header:
            col_index = header.index(today)
        else:
            col_index = len(header)
            while len(values[3]) <= col_index:
                values[3].append("")
            values[3][col_index] = today

            while len(values[4]) <= col_index:
                values[4].append("")
            values[4][col_index] = "0"

            print(f"Создан новый столбец для {today}")

        row_index = 6
        while row_index < len(values):
            while len(values[row_index]) <= col_index:
                values[row_index].append("")
            if not values[row_index][col_index]:
                break
            row_index += 1

        if len(values) <= row_index:
            values.append([])
            while len(values[row_index]) <= col_index:
                values[row_index].append("")

        values[row_index][col_index] = str(value)
        print(f"Добавлено значение {value} в {today} (строка {row_index+1})")

        total = 0.0
        for r in range(6, min(len(values), 1000)):
            try:
                total += float(values[r][col_index])
            except (ValueError, IndexError):
                pass
        values[4][col_index] = str(total)
        print(f"✅ Обновлена сумма: {total}")

        url_update = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{SHEET_NAME}!A1:ZZ1000?valueInputOption=RAW"
        async with session.put(url_update, json={"values": values}) as resp:
            result = await resp.json()
            print("📊 Google Sheets обновлён:", result.get("updatedRange", "OK"))

async def get_total_sum_for_date(target_date: str):
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        url_get = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{SHEET_NAME}!A1:ZZ6"
        async with session.get(url_get) as resp:
            data = await resp.json()
        values = data.get("values", [])
        if len(values) < 5:
            return 0.0
        header = values[3] if len(values) > 3 else []
        if target_date not in header:
            return 0.0
        col_index = header.index(target_date)
        if len(values[4]) <= col_index:
            return 0.0
        try:
            return float(values[4][col_index])
        except ValueError:
            return 0.0

async def main():
    await update_google_sheet(4.5)
    print(await get_total_sum_for_date("08.11.2025"))

if __name__ == "__main__":
    asyncio.run(main())