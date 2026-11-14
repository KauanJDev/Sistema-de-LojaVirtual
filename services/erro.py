from fastapi import HTTPException

def erro_404(registro, mensagem):
    if registro is None:
        raise HTTPException(status_code=404, detail=mensagem)
    return registro