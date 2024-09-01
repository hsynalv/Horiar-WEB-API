from authlib.integrations.flask_client import OAuth

oauth = OAuth()

def configure_oauth(app):
    oauth.init_app(app)
    oauth.register(
        name='discord',
        client_id=app.config['DISCORD_CLIENT_ID'],
        client_secret=app.config['DISCORD_CLIENT_SECRET'],
        authorize_url='https://discord.com/api/oauth2/authorize',
        access_token_url='https://discord.com/api/oauth2/token',
        redirect_uri='http://127.0.0.1:5000/login/discord/callback',# TODO: Geri Dönüşü burada ve discord dev de düzeltmek gerek
        client_kwargs={'scope': 'identify email'}
    )
