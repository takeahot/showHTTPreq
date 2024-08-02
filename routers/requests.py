from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from aiolimiter import AsyncLimiter
import json
import os
import pprint
import datetime
import httpx
import models
from dependencies import get_db
from utils import CustomJSONEncoder
from rate_limiter import limiter
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

router = APIRouter()

domains = [
    "https://morzhkzdhj3oi.elma365.eu"
]

ALLOWED_BROWSERS = ["chrome", "opera", "firefox", "safari", "edge"]

# Путь к уже смонтированным статическим файлам
static_files_path = "/static"

async def handle_request(request: Request, db: Session, method: str):
    try:
        user_agent = request.headers.get("User-Agent", "").lower()
        
        # Проверка User-Agent и возврат index.html из смонтированных статических файлов
        if any(browser in user_agent for browser in ["chrome", "opera", "firefox", "safari", "edge"]):
            index_file_path = os.path.join(static_files_path, "index.html")
            return FileResponse(index_file_path, media_type="text/html")

        # Продолжаем с обработкой логов и пересылкой запроса
        bodyObj = await request.json()
        db_logs = models.Logs(
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            httpmethod=method,
            headers=json.dumps(dict(request.headers), cls=CustomJSONEncoder),
            body=json.dumps(bodyObj),
            path_params=repr(request.path_params),
            query_params=json.dumps(dict(request.query_params))
        )
        db.add(db_logs)
        db.commit()
        db.refresh(db_logs)

        if not hasattr(bodyObj, 'get') or not callable(getattr(bodyObj, 'get')) or str(bodyObj.get('eventName')) not in [
            'ticket_created',
            'ticket_updated',
            'ticket_comment_created',
            'ticket_comment_updated'
        ]:
            print('Request received:', str(bodyObj['eventName']))
            try:
                return 'Request received:' + json.dumps(bodyObj)
            except Exception as e:
                return 'Request received not json:' + str(bodyObj)
        else:
            print('Request received for resend:', str(bodyObj['eventName']))

            headers_dict = dict(request.headers)
            headers_dict.pop('content-length', None)
            headers_dict.pop('host', None)

            elma_tail = bodyObj['eventName']
            bodyObj = {**bodyObj, 'eventName': f"{elma_tail}_from_koyeb_to_ELMA"}

            response_datas = []
            for domain in domains:
                async with limiter:
                    async with httpx.AsyncClient() as client:
                        try:
                            print(
                                'query parameter for ELMA',
                                {
                                    'method': method,
                                    'url': f"{domain}/api/extensions/22fe87c3-14fc-4c97-83dd-52ef65fa4644/script/{elma_tail}",
                                    'headers': headers_dict,
                                    'json': bodyObj
                                }
                            )
                            
                            db_request_logs = models.Logs(
                                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
                                httpmethod=method,
                                headers=json.dumps(headers_dict, cls=CustomJSONEncoder),
                                body=json.dumps(bodyObj),
                                path_params=repr(request.path_params),
                                query_params=json.dumps(dict(request.query_params))
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

                            db_response_logs = models.Logs(
                                timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
                                httpmethod=method,
                                headers=json.dumps(dict(external_response.headers), cls=CustomJSONEncoder),
                                body=json.dumps(response_data),
                                path_params=repr(request.path_params),
                                query_params=json.dumps(dict(request.query_params))
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
