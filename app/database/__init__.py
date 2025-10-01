from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

#en este archivo se define las extensiones de la bd y las migracion
db = SQLAlchemy()
migrate = Migrate()

#recibe un objeto app, creo que es la aplicacion, luego de eso ,parece que inicia la bd y la migracion
def init_db(app):
    #el init_app creo que son funciones definidas
    db.init_app(app)#configura SQLAlchemy con la aplicacion flask,necesario para interactuar con la base de datos en la aplicacion
    migrate.init_app(app, db)
    
