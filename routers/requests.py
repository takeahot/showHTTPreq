from fastapi import APIRouter, Request, HTTPException, Depends
import json
import pprint
import datetime
import httpx
from sqlalchemy.orm import Session
import models
from dependencies import get_db
from utils import CustomJSONEncoder

router = APIRouter()

domains = [
    "https://7isfa26wfvp4a.elma365.eu",
    "https://morzhkzdhj3oi.elma365.eu"
]

@router.api_route('/', methods=['GET', 'PUT', 'POST', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS', 'TRACE', 'CONNECT'])
async def write_request(request: Request, db: Session = Depends(get_db)):
    try:
        bodyObj = await request.json()
        db_logs = models.Logs(
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            httpmethod=request.method,
            headers=json.dumps(dict(request.headers), cls=CustomJSONEncoder),
            body=json.dumps(bodyObj),
            path_params=repr(request.path_params),
            query_params=json.dumps(dict(request.query_params))
        )
        db.add(db_logs)
        db.commit()
        db.refresh(db_logs)

        if str(bodyObj.get('eventName')) not in [
            'ticket_created',
            'ticket_updated',
            'ticket_comment_created',
            'ticket_comment_updated'
        ]:
            print('Request received:', str(bodyObj['eventName']))
        else:
            print('Request received for resend:', str(bodyObj['eventName']))

            headers_dict = dict(request.headers)
            headers_dict.pop('content-length', None)
            headers_dict.pop('host', None)

            # pprint.pprint(bodyObj)
            timeout = httpx.Timeout(60.0, connect=20.0, read=60.0)

            for domain in domains:
                async with httpx.AsyncClient() as client:
                    try:
                        print(
                            'query parameter for ELMA',
                            {
                                'method': request.method,
                                'url': f"{domain}/api/extensions/22fe87c3-14fc-4c97-83dd-52ef65fa4644/script/{bodyObj['eventName']}",
                                'headers': headers_dict,
                                'json': bodyObj
                            }
                        )
                        external_response = await client.request(
                            method=request.method,
                            url=f"{domain}/api/extensions/22fe87c3-14fc-4c97-83dd-52ef65fa4644/script/{bodyObj['eventName']}",
                            headers=headers_dict,
                            json=bodyObj,
                            timeout=timeout
                        )
                        response_data = {}
                        if not (200 <= external_response.status_code < 300):
                            response_data['payload'] = {
                                'textError': f"data:text/html,{external_response.text}"
                            }
                        else:
                            response_data = external_response.json()

                        response_data['status_code'] = external_response.status_code
                        response_data['eventName'] = bodyObj['eventName'] + "_response"

                        db_response_logs = models.Logs(
                            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
                            httpmethod=request.method,
                            headers=json.dumps(dict(external_response.headers), cls=CustomJSONEncoder),
                            body=json.dumps(response_data),
                            path_params=repr(request.path_params),
                            query_params=json.dumps(dict(request.query_params))
                        )
                        db.add(db_response_logs)
                        db.commit()
                        db.refresh(db_response_logs)

                        print('Request and response logged')
                        print(response_data)
                    except httpx.RequestError as exc:
                        print(f"An error occurred while requesting {exc.request.url!r}.")
                        raise HTTPException(status_code=500, detail=f"Request to external service failed: {str(exc)}")

        return {
            'method': request.method,
            "headers": request.headers,
            "body": bodyObj,
            "path_params": request.path_params,
            "query_params": request.query_params
        }
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
