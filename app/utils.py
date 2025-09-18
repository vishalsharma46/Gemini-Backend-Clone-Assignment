from fastapi import HTTPException, status

def api_ok(data=None, message: str = "ok"):
    return {"ok": True, "message": message, "data": data}

def api_error(message: str, code: int = status.HTTP_400_BAD_REQUEST):
    raise HTTPException(status_code=code, detail={"ok": False, "message": message})
