import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import ssl # Necesario para crear un contexto de conexión segura

# --- CONFIGURACIÓN DE CREDENCIALES Y SERVIDOR ---
# IMPORTANTE: Cambia estas variables por tu configuración real.
# IDEALMENTE, DEBERÍAS CARGARLAS DESDE UN ARCHIVO .env POR SEGURIDAD.
# El email debe ser una dirección completa.
SENDER_EMAIL = "noreply.notificaciones.3en1@gmail.com" 
SENDER_APP_PASSWORD = "cvzh gqfp lypp hlol" # Contraseña de aplicación generada en Gmail

# Usamos la configuración SMTP más confiable para Gmail (SSL implícito)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465 


# FUNCIÓN PRINCIPAL DE ENVÍO
def send_email_notification(recipient_email, game_name, score, player_name=None):
    """
    Envía una notificación de récord por correo electrónico en formato HTML y texto plano.
    
    Parámetros:
    - recipient_email (str): El correo del destinatario.
    - game_name (str): Nombre del juego donde se batió el récord.
    - score (int): El puntaje alcanzado.
    - player_name (str, opcional): Nombre del jugador.
    """
    # Si no se pasa nombre, usar el del email (antes del @) como respaldo.
    if not player_name:
        try:
            player_name = recipient_email.split('@')[0]
        except:
            player_name = "Jugador" # Fallback por si el email no es válido

    # Asunto del correo
    subject = f"🏆 ¡Nuevo récord superado en {game_name}!"

    # Cuerpo del mensaje (texto plano)
    text_content = f"""
¡Felicidades {player_name}! 🎉

Has alcanzado el primer puesto en el juego {game_name} con un puntaje de {score} puntos.  
¡Eres el nuevo TOP 1° del ranking!

Sigue jugando y defiende tu posición.
"""

    # Cuerpo del mensaje en HTML (Mejor presentación visual)
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color:#f4f4f4; padding:20px;">
        <div style="max-width:600px; margin:auto; background:#fff; border-radius:8px; padding:20px; border:1px solid #ddd;">
            <h2 style="color:#2b6cb0; text-align:center;">🏆 ¡Nuevo Récord Superado!</h2>
            <p style="font-size:16px; color:#333;">
                <b>¡Felicidades, {player_name}!</b><br>
                Has alcanzado el <b>primer puesto</b> en el juego 
                <span style="color:#2b6cb0; font-weight:bold;">{game_name}</span> 
                con un impresionante puntaje de <b>{score:,}</b> puntos.
            </p>
            <p style="font-size:15px; color:#333;">
                Eres el nuevo campeón del ranking.<br>
                ¡Sigue jugando y defiende tu posición!
            </p>
            <hr style="margin:20px 0;">
            <p style="font-size:13px; color:#888; text-align:center;">
                Este mensaje fue enviado automáticamente por el sistema de puntuaciones del juego 3 en 1.
            </p>
        </div>
    </body>
    </html>
    """

    # Crear mensaje MIME multipart (para enviar HTML y texto plano)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    
    # --- MODIFICACIÓN ANTI-SPAM CLAVE 1 ---
    # Usamos un nombre de remitente amigable, pero que se autentique correctamente.
    # Esta estructura ("Nombre Amigable <email@dominio.com>") reduce la probabilidad de ser marcado como spam.
    msg["From"] = f"Notificaciones 3 en 1 <{SENDER_EMAIL}>"
    msg["To"] = recipient_email

    # Adjuntar las dos versiones del mensaje (Texto plano y HTML)
    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        # --- MODIFICACIÓN ANTI-SPAM CLAVE 2 ---
        # Usamos smtplib.SMTP_SSL y el puerto 465. 
        # Esta conexión cifrada implícita es muy confiable con Gmail y reduce el riesgo de spam.
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email enviado correctamente a {recipient_email}")

    except Exception as e:
        print(f"⚠️ Error al enviar correo a {recipient_email}: {e}")