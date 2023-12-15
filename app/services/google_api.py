from datetime import datetime

from aiogoogle import Aiogoogle

from app.core.config import settings

# Константа с форматом строкового представления времени
FORMAT = "%Y/%m/%d %H:%M:%S"


async def spreadsheets_create(wrapper_services: Aiogoogle) -> str:
    # Экземпляр класса Resource
    service = await wrapper_services.discover("sheets", "v4")
    # Тело запроса
    spreadsheet_body = {
        "properties": {"title": "Инвестирование", "locale": "ru_RU"},
        "sheets": [
            {
                "properties": {
                    "sheetType": "GRID",
                    "sheetId": 0,
                    "title": "Отчет",
                    "gridProperties": {"rowCount": 20, "columnCount": 4},
                }
            }
        ],
    }
    response = await wrapper_services.as_service_account(
        service.spreadsheets.create(json=spreadsheet_body)
    )
    spreadsheetid = response["spreadsheetId"]
    return spreadsheetid


async def set_user_permissions(
    spreadsheetid: str, wrapper_services: Aiogoogle
) -> None:
    permissions_body = {
        "type": "user",
        "role": "writer",
        "emailAddress": settings.email,
    }
    service = await wrapper_services.discover("drive", "v3")
    await wrapper_services.as_service_account(
        service.permissions.create(
            fileId=spreadsheetid, json=permissions_body, fields="id"
        )
    )


async def spreadsheets_update_value(
    spreadsheetid: str, project_list: list, wrapper_services: Aiogoogle
) -> None:
    now_date_time = datetime.now().strftime(FORMAT)
    service = await wrapper_services.discover("sheets", "v4")
    # Шапка таблицы
    table_values = [
        ["Отчёт от", now_date_time],
        ["ТОП выполненных проектов (время сбора)"],
        ["Название проекта", "Время сбора", "Описание", "Сумма"],
    ]
    # Список значений для строк таблицы
    for project in project_list:
        new_row = [
            str(project[0]),
            str(project[2]),
            str(project[3]),
            str(project[4]),
        ]
        table_values.append(new_row)
    print(table_values)

    update_body = {"majorDimension": "ROWS", "values": table_values}

    await wrapper_services.as_service_account(
        service.spreadsheets.values.update(
            spreadsheetId=spreadsheetid,
            range="A1:D100",
            valueInputOption="USER_ENTERED",
            json=update_body,
        )
    )
