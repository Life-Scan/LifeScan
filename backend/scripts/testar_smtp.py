"""Script para testar o envio de email via SMTP.

Uso:
  python -m scripts.testar_smtp --para seu-email@exemplo.com
"""

import argparse
import sys

from app.core.config import obter_configuracoes
from app.services.email import ErroEnvioEmail, enviar_email


def main() -> None:
    parser = argparse.ArgumentParser(description="Testa o envio de email (console ou SMTP).")
    parser.add_argument(
        "--para",
        required=True,
        help="Email de destino para receber a mensagem de teste.",
    )
    parser.add_argument(
        "--assunto",
        default="[LifeScan] Teste de Configuração SMTP",
        help="Assunto do email de teste.",
    )

    args = parser.parse_args()
    config = obter_configuracoes()

    print("\n" + "=" * 60)
    print(" Configurações de Email Atuais:")
    print("=" * 60)
    print(f" Modo (EMAIL_MODE):     {config.modo_email}")
    print(f" Remetente (EMAIL_FROM): {config.remetente_email}")
    print(f" SMTP Host:              {config.smtp_host}")
    print(f" SMTP Porta:             {config.smtp_port}")
    print(f" SMTP Usuário:           {config.smtp_user or '(não informado)'}")
    print(f" SMTP Senha:             {'******' if config.smtp_password else '(não informada)'}")
    print(f" SMTP STARTTLS:          {config.smtp_tls}")
    print(f" SMTP SSL Direto:        {config.smtp_ssl}")
    print(f" SMTP Timeout:           {config.smtp_timeout}s")
    print("=" * 60 + "\n")

    if config.modo_email != "smtp":
        print("AVISO: O modo atual é 'console'. Para envio real, defina EMAIL_MODE=smtp no arquivo .env.")
        print("Prosseguindo no modo configurado...\n")

    corpo = (
        "Olá!\n\n"
        "Este é um email de teste enviado pelo sistema LifeScan para validar "
        "as configurações de conexão SMTP.\n\n"
        "Se você recebeu esta mensagem, o envio de emails está funcionando perfeitamente!\n"
    )

    corpo_html = (
        "<div style='font-family: sans-serif; line-height: 1.5; color: #333;'>"
        "  <h2 style='color: #0d9488;'>LifeScan - Teste de Conexão SMTP</h2>"
        "  <p>Olá!</p>"
        "  <p>Este é um email de teste enviado pelo sistema <strong>LifeScan</strong> para validar as configurações de conexão SMTP.</p>"
        "  <p style='background: #f0fdfa; border-left: 4px solid #0d9488; padding: 12px; margin: 16px 0;'>"
        "    ✅ Se você recebeu esta mensagem, o envio de emails está funcionando perfeitamente!"
        "  </p>"
        "</div>"
    )

    print(f"Enviando email de teste para '{args.para}'...")
    try:
        enviar_email(
            destinatario=args.para,
            assunto=args.assunto,
            corpo=corpo,
            corpo_html=corpo_html,
        )
        print("\n[OK] Sucesso! O email foi processado sem erros.")
    except ErroEnvioEmail as e:
        print(f"\n[ERRO] Falha no envio de email: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERRO] Erro inesperado: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
