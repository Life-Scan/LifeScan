"""Envio de emails.

Por enquanto existe apenas o modo "console" (EMAIL_MODE=console), usado no
desenvolvimento: o email é mostrado no terminal da API em vez de ser enviado.
O envio real por SMTP entra aqui depois, sem mudar quem chama enviar_email().
"""

from collections import deque
from dataclasses import dataclass

from app.core.config import obter_configuracoes


@dataclass(frozen=True)
class Email:
    destinatario: str
    assunto: str
    corpo: str


# Últimos emails "enviados" no modo console (usado pelos testes e para depuração)
caixa_de_saida: deque[Email] = deque(maxlen=50)


def enviar_email(destinatario: str, assunto: str, corpo: str) -> None:
    config = obter_configuracoes()
    if config.modo_email != "console":
        raise RuntimeError(
            f"EMAIL_MODE={config.modo_email!r} ainda não é suportado. Use EMAIL_MODE=console."
        )

    email = Email(destinatario=destinatario, assunto=assunto, corpo=corpo)
    caixa_de_saida.append(email)
    linha = "=" * 64
    print(
        f"\n{linha}\n[EMAIL - modo console, nada foi enviado]\n"
        f"De:      {config.remetente_email}\nPara:    {destinatario}\nAssunto: {assunto}\n\n{corpo}\n{linha}\n",
        flush=True,
    )
