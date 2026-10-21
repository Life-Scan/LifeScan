"""Script para testar o envio de email via SMTP com o template HTML do LifeScan.

Uso:
  python -m scripts.testar_smtp --para seu-email@exemplo.com
  python -m scripts.testar_smtp --para seu-email@exemplo.com --nome "Arthur Ivo"
"""

import argparse
import sys

from app.core.config import obter_configuracoes
from app.services.email import ErroEnvioEmail, enviar_email


def main() -> None:
    parser = argparse.ArgumentParser(description="Testa o envio de email com template HTML do LifeScan.")
    parser.add_argument(
        "--para",
        required=True,
        help="Email de destino para receber a mensagem de teste.",
    )
    parser.add_argument(
        "--nome",
        default="Arthur Ivo",
        help="Nome a ser exibido na saudação do email (padrão: Arthur Ivo).",
    )
    parser.add_argument(
        "--senha",
        default="NEy74nBRMM",
        help="Senha provisória exibida no email de teste (padrão: NEy74nBRMM).",
    )
    parser.add_argument(
        "--assunto",
        default="Seu acesso ao LifeScan",
        help="Assunto do email de teste (padrão: 'Seu acesso ao LifeScan').",
    )

    args = parser.parse_args()
    config = obter_configuracoes()

    print("\n" + "=" * 60)
    print(" Configurações de Email Atuais:")
    print("=" * 60)
    print(f" Modo (EMAIL_MODE):      {config.modo_email}")
    print(f" Remetente (EMAIL_FROM): {config.remetente_email}")
    print(f" SMTP Host:              {config.smtp_host}")
    print(f" SMTP Porta:             {config.smtp_port}")
    print(f" SMTP Usuário:           {config.smtp_user or '(não informado)'}")
    print(f" SMTP Senha:             {'******' if config.smtp_password else '(não informada)'}")
    print(f" SMTP STARTTLS:          {config.smtp_tls}")
    print(f" SMTP SSL Direto:        {config.smtp_ssl}")
    print(f" SMTP Timeout:           {config.smtp_timeout}s")
    print(f" Destinatário:           {args.para}")
    print(f" Nome exibido:           {args.nome}")
    print("=" * 60 + "\n")

    if config.modo_email != "smtp":
        print("AVISO: O modo atual é 'console'. Para envio real, defina EMAIL_MODE=smtp no arquivo .env.")
        print("Prosseguindo no modo configurado...\n")

    corpo_texto = (
        f"Olá, {args.nome}!\n\n"
        "Seu médico criou um acesso para você no sistema LifeScan, onde seu tratamento e histórico são acompanhados.\n\n"
        f"Email de acesso: {args.para}\n"
        f"Senha provisória: {args.senha}\n\n"
        "Esta senha provisória é válida por 7 dias. Ao acessar pela primeira vez, você definirá sua senha definitiva.\n\n"
        f"Acesse em: {config.url_frontend}/login\n\n"
        "Se você não esperava este email, por favor ignore esta mensagem."
    )

    corpo_html = (
        "<div style=\"background-color: #f8fafc; padding: 40px 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;\">\n"
        "  <div style=\"max-width: 580px; margin: 0 auto; background-color: #ffffff; padding: 32px; border: 1px solid #e2e8f0; border-radius: 8px; color: #1e293b; box-shadow: 0 1px 3px rgba(0,0,0,0.04);\">\n"
        "    <div style=\"border-bottom: 2px solid #0d9488; padding-bottom: 14px; margin-bottom: 24px;\">\n"
        "      <h1 style=\"color: #0d9488; font-size: 24px; font-weight: 700; margin: 0; letter-spacing: -0.5px;\">LifeScan</h1>\n"
        "    </div>\n"
        f"    <p style=\"font-size: 16px; color: #1e293b; margin: 0 0 16px 0; line-height: 1.5;\">Olá, <strong>{args.nome}</strong>!</p>\n"
        "    <p style=\"font-size: 15px; color: #334155; margin: 0 0 24px 0; line-height: 1.6;\">Seu médico criou um acesso para você no sistema <strong>LifeScan</strong>, onde seu tratamento e histórico são acompanhados.</p>\n"
        "    <div style=\"background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px 20px; margin: 24px 0;\">\n"
        f"      <p style=\"margin: 0 0 10px 0; font-size: 14px; color: #1e293b; line-height: 1.5;\"><strong>Email de acesso:</strong> <a href=\"mailto:{args.para}\" style=\"color: #0284c7; text-decoration: underline;\">{args.para}</a></p>\n"
        f"      <p style=\"margin: 0; font-size: 14px; color: #1e293b; line-height: 1.5;\"><strong>Senha provisória:</strong> <code style=\"background-color: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 4px; font-size: 15px; font-weight: 700; font-family: Consolas, 'Liberation Mono', Menlo, Courier, monospace; letter-spacing: 0.5px; display: inline-block;\">{args.senha}</code></p>\n"
        "    </div>\n"
        "    <p style=\"font-size: 14px; color: #64748b; margin: 20px 0; line-height: 1.6;\">Esta senha provisória é válida por <strong>7 dias</strong>. Ao acessar pela primeira vez, você definirá sua senha definitiva.</p>\n"
        "    <div style=\"margin: 32px 0; text-align: center;\">\n"
        f"      <a href=\"{config.url_frontend}/login\" style=\"background-color: #0d9488; color: #ffffff; padding: 12px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 15px; display: inline-block;\">Acessar o LifeScan</a>\n"
        "    </div>\n"
        "    <hr style=\"border: 0; border-top: 1px solid #f1f5f9; margin: 28px 0 20px 0;\" />\n"
        "    <p style=\"font-size: 12px; color: #94a3b8; text-align: center; margin: 0; line-height: 1.4;\">Se você não esperava este email, por favor ignore esta mensagem.</p>\n"
        "  </div>\n"
        "</div>"
    )

    print(f"Enviando email com template HTML para '{args.para}'...")
    try:
        enviar_email(
            destinatario=args.para,
            assunto=args.assunto,
            corpo=corpo_texto,
            corpo_html=corpo_html,
        )
        print("\n[OK] Sucesso! O email formatado em HTML foi enviado com sucesso.")
    except ErroEnvioEmail as e:
        print(f"\n[ERRO] Falha no envio de email: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERRO] Erro inesperado: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

