from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from aiolimiter import AsyncLimiter
import json
import os
import datetime
import httpx
import models
from dependencies import get_db
from utils import CustomJSONEncoder
from rate_limiter import limiter
from fastapi.responses import FileResponse

router = APIRouter()

domains = [
    "https://morzhkzdhj3oi.elma365.eu",
    # "https://7isfa26wfvp4a.elma365.eu"
]

ALLOWED_BROWSERS = ["chrome", "opera", "firefox", "safari", "edge"]

# Путь к папке static, где теперь лежат сгенерированные файлы React
static_files_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))

async def handle_request(request: Request, db: Session, method: str):
    try:
        # Продолжаем с обработкой логов и пересылкой запроса
        bodyObj = dict()
        if request.headers.get("content-length") and int(request.headers.get("content-length")) > 0:
            bodyObj = await request.json()

        if bodyObj.keys().__len__  and hasattr(bodyObj, 'get') and str(bodyObj.get('eventName')) != "None":
            event_name = bodyObj.get('eventName')
        else:
            event_name = ""

        if bodyObj.keys().__len__ and hasattr(bodyObj, 'get') and str(bodyObj.get('eventId')) != "None":
            event_id = bodyObj.get('eventId')
        else:
            event_id = ""

        domain = request.headers.get('x-origin-domain')
        client_ip = request.client.host
        if client_ip == "52.28.237.77":
            domain = "CASAVI"

        print(f"Got request: {client_ip} {domain} {request.method} {request.url} {event_name} {event_id}")

        user_agent = request.headers.get("User-Agent", "").lower()
                   
        # Проверка User-Agent и возврат index.html
        if any(browser in user_agent for browser in ALLOWED_BROWSERS):
            index_file_path = os.path.join(static_files_path, "index.html")
            print ("front")
            return FileResponse(index_file_path, media_type="text/html")

       # print(json.dumps(bodyObj, ensure_ascii=False))
        db_logs = models.Logs(
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            httpmethod=method,
            headers=json.dumps(dict(request.headers), ensure_ascii=False, cls=CustomJSONEncoder),
            body=json.dumps(bodyObj, ensure_ascii=False),
            path_params=repr(request.path_params),
            query_params=json.dumps(dict(request.query_params), ensure_ascii=False)
        )
        db.add(db_logs)
        db.commit()
        db.refresh(db_logs)

        if not hasattr(bodyObj, 'get') or str(bodyObj.get('eventName')) not in [
            'ticket_created',
            'ticket_updated',
            'ticket_comment_created',
            'ticket_comment_updated'
        ]:
            # print('Request received:', str(bodyObj['eventName']))
            return 'Request received:' + json.dumps(bodyObj, ensure_ascii=False)

        else:
            headers_dict = dict(request.headers)
            headers_dict.pop('content-length', None)
            headers_dict.pop('host', None)
            headers_dict["x-forwarded-for"] = "0.0.0.0"
            headers_dict["x-origin-domain"] = "koyeb"

            elma_tail = bodyObj['eventName']
            bodyObj = {**bodyObj, 'eventName': f"{elma_tail}_from_koyeb_to_ELMA"}

            response_datas = []
            for domain in domains:
                async with limiter:
                    async with httpx.AsyncClient() as client:
                        try:
                            db_request_logs = models.Logs(
                                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
                                httpmethod=method,
                                headers=json.dumps(headers_dict, ensure_ascii=False, cls=CustomJSONEncoder),
                                body=json.dumps(bodyObj, ensure_ascii=False),
                                path_params=repr(request.path_params),
                                query_params=json.dumps(dict(request.query_params), ensure_ascii=False)
                            )
                            db.add(db_request_logs)
                            db.commit()
                            db.refresh(db_request_logs)

                            external_response = await client.request(
                                method=method,
                                url=f"{domain}/api/extensions/22fe87c3-14fc-4c97-83dd-52ef65fa4644/script/{elma_tail}",
                                headers=headers_dict,
                                json=bodyObj,
                            )
                            response_data = {}
                            if not (200 <= external_response.status_code < 300):
                                response_data['payload'] = {
                                    'textError': f"data:text/html,{external_response.text}",
                                    'reqest': {
                                        'method': method,
                                        'url': f"{domain}/api/extensions/22fe87c3-14fc-4c97-83dd-52ef65fa4644/script/{elma_tail}",
                                        'headers': headers_dict,
                                        'json': bodyObj
                                    }
                                }
                            else:
                                response_data = external_response.json()

                            response_data['status_code'] = external_response.status_code
                            response_data['eventName'] = bodyObj['eventName'] + "_response"
                            external_response.headers['x-origin-domain'] = "res <- ELMA"

                            db_response_logs = models.Logs(
                                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
                                httpmethod=method,
                                headers=json.dumps(dict(external_response.headers), ensure_ascii=False, cls=CustomJSONEncoder),
                                body=json.dumps(response_data, ensure_ascii=False),
                                path_params=repr(request.path_params),
                                query_params=json.dumps(dict(request.query_params, ensure_ascii=False))
                            )
                            db.add(db_response_logs)
                            db.commit()
                            db.refresh(db_response_logs)

                            print('Request and response logged')
                            print('response data: ', response_data)
                        except httpx.RequestError as exc:
                            print(f"An error occurred while requesting {exc.request.url!r}.")
                            raise HTTPException(status_code=500, detail=f"Request to external service failed: {str(exc)}")
                response_datas = response_datas + [response_data]
            return response_datas
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/', operation_id="root_request_get")
async def write_request_get(request: Request, db: Session = Depends(get_db)):
    return await handle_request(request, db, "GET")

@router.put('/', operation_id="root_request_put")
async def write_request_put(request: Request, db: Session = Depends(get_db)):
    return await handle_request(request, db, "PUT")

@router.post('/', operation_id="root_request_post")
async def write_request_post(request: Request, db: Session = Depends(get_db)):
    return await handle_request(request, db, "POST")

@router.delete('/', operation_id="root_request_delete")
async def write_request_delete(request: Request, db: Session = Depends(get_db)):
    return await handle_request(request, db, "DELETE")

@router.patch('/', operation_id="root_request_patch")
async def write_request_patch(request: Request, db: Session = Depends(get_db)):
    return await handle_request(request, db, "PATCH")

@router.head('/', operation_id="root_request_head")
async def write_request_head(request: Request, db: Session = Depends(get_db)):
    return await handle_request(request, db, "HEAD")

@router.options('/', operation_id="root_request_options")
async def write_request_options(request: Request, db: Session = Depends(get_db)):
    return await handle_request(request, db, "OPTIONS")

# @router.get('/x/', operation_id="root_request_get")
# async def write_request_get(request: Request, db: Session = Depends(get_db)):
#     return await handle_request(request, db, "GET")

# @router.put('/x/', operation_id="root_request_put")
# async def write_request_put(request: Request, db: Session = Depends(get_db)):
#     return await handle_request(request, db, "PUT")

# @router.post('/x/', operation_id="root_request_post")
# async def write_request_post(request: Request, db: Session = Depends(get_db)):
#     return await handle_request(request, db, "POST")

# @router.delete('/x/', operation_id="root_request_delete")
# async def write_request_delete(request: Request, db: Session = Depends(get_db)):
#     return await handle_request(request, db, "DELETE")

# @router.patch('/x/', operation_id="root_request_patch")
# async def write_request_patch(request: Request, db: Session = Depends(get_db)):
#     return await handle_request(request, db, "PATCH")

# @router.head('/x/', operation_id="root_request_head")
# async def write_request_head(request: Request, db: Session = Depends(get_db)):
#     return await handle_request(request, db, "HEAD")

# @router.options('/x/', operation_id="root_request_options")
# async def write_request_options(request: Request, db: Session = Depends(get_db)):
#     return await handle_request(request, db, "OPTIONS")