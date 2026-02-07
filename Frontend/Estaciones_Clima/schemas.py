from extensions import ma, db
from marshmallow import fields, validate
# Asegúrate de que en models.py ya tengas la clase Estacion creada
from models import Estacion 

class EstacionSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Estacion
        load_instance = True
        sqla_session = db.session

    # id: Solo lectura (dump_only) porque lo genera la base de datos
    id = ma.auto_field(dump_only=True)
    
    # Validaciones básicas
    nombre = ma.auto_field(required=True, validate=validate.Length(min=1, max=255))
    
    # Validaciones lógicas para fechas
    dia = fields.Integer(required=True, validate=validate.Range(min=1, max=31))
    mes = fields.Integer(required=True, validate=validate.Range(min=1, max=12))
    anio = fields.Integer(required=True, validate=validate.Range(min=2000, max=2100))
    
    # Coordenadas
    latitud = fields.Float(required=True)
    longitud = fields.Float(required=True)

# Inicialización de esquemas
estacion_schema = EstacionSchema()
estaciones_schema = EstacionSchema(many=True)