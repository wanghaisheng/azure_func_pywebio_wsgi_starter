import azure.functions as func

from .add_url_rule import app
# from .route import app

def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    return func.WsgiMiddleware(app.wsgi_app).handle(req, context)

