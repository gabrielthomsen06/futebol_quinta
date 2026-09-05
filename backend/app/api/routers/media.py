"""As fotos, quando elas não estão no disco da própria aplicação.

Com `STORAGE_BACKEND=local` quem serve `/media` é o `StaticFiles` montado em
`main.py`, exatamente como antes. Com `r2`, o arquivo está em outro domínio e
esta rota apenas aponta para lá.

O redirecionamento é o que mantém a mudança barata: `photo_path` continua sendo
o caminho relativo gravado no banco, os schemas não mudam e o frontend segue
pedindo `/media/<caminho>` como sempre pediu. Trocar isso por uma URL absoluta
na resposta da API é mais rápido — uma requisição a menos — mas mexeria em
schemas e componentes sem necessidade para validar o Heroku.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse

from app.services.storage import get_storage

router = APIRouter(tags=["media"])


@router.get("/{rel_path:path}", include_in_schema=False)
def get_media(rel_path: str) -> RedirectResponse:
    # O caminho vem do banco, não do usuário, mas a guarda custa uma linha e
    # fecha a porta para uma chave montada à mão.
    if not rel_path or ".." in rel_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Arquivo não encontrado.")

    # Sem consultar o R2 antes: um objeto ausente devolve 404 lá, e o
    # PlayerAvatar já trata a falha mostrando as iniciais. Conferir aqui
    # custaria uma ida à rede em toda foto exibida.
    return RedirectResponse(get_storage().url_for(rel_path), status_code=302)
