"""Descriptor-backed downloads shared by HTTP and MCP, with late TTL checks."""

import anyio

from fastapi import HTTPException
from starlette.responses import JSONResponse, StreamingResponse

from backend.services.storage import TemporaryStorage
from backend.utils.mime import content_type_for_path

DOWNLOAD_HEADERS = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}


def download_error(error: HTTPException):
    return JSONResponse({"detail": error.detail}, status_code=error.status_code,
                        headers={**(error.headers or {}), **DOWNLOAD_HEADERS})


class ResultDownloadResponse(StreamingResponse):
    def __init__(self, storage: TemporaryStorage, token: str, missing_detail: str):
        self.storage, self.token, self.missing_detail = storage, token, missing_detail
        super().__init__(iter(()), headers=DOWNLOAD_HEADERS)

    async def __call__(self, scope, receive, send):
        # FileResponse opens a path later. Instead validate/open here, before
        # response headers, and keep that descriptor for the entire delivery.
        # Shield short filesystem operations from cancellation so returned
        # descriptors cannot be abandoned by a cancelled worker await.
        opened = await anyio.to_thread.run_sync(self.storage.open_result, self.token)
        if opened is None:
            return await download_error(HTTPException(404, self.missing_detail))(scope, receive, send)
        file, path = opened

        async def chunks():
            while True:
                chunk = await anyio.to_thread.run_sync(file.read, 64 * 1024)
                if not chunk:
                    break
                yield chunk

        try:
            if self.storage._now() >= file.expires_at:
                return await download_error(HTTPException(404, self.missing_detail))(scope, receive, send)
            self.media_type = content_type_for_path(path.suffix)
            self.init_headers({**DOWNLOAD_HEADERS,
                               "Content-Disposition": f'attachment; filename="konvertira-cleaned{path.suffix}"'})
            self.body_iterator = chunks()
            self._expires_at = file.expires_at
            await super().__call__(scope, receive, send)
        finally:
            # Includes disconnect, cancellation, read/send exceptions and success.
            file.close()

    async def stream_response(self, send):
        # The final check is at response-start, not handler/path-resolution time.
        if self.storage._now() >= self._expires_at:
            error = download_error(HTTPException(404, self.missing_detail))
            await send({"type": "http.response.start", "status": 404,
                        "headers": error.raw_headers})
            await send({"type": "http.response.body", "body": error.body, "more_body": False})
            return
        await super().stream_response(send)
