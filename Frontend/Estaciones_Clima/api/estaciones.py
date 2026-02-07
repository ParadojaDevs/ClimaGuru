from flask import request
from flask_restful import Resource
from marshmallow import ValidationError

from extensions import db
from models import Estacion
from schemas import estacion_schema, estaciones_schema
from . import api

class EstacionList(Resource):
    # GET /api/estaciones
    def get(self):
        # Ordenamos por ID ascendente
        estaciones = Estacion.query.order_by(Estacion.id.asc()).all()
        return estaciones_schema.dump(estaciones), 200

    # POST /api/estaciones
    def post(self):
        data = request.get_json()
        if not data:
            return {"message": "Cuerpo JSON requerido."}, 400
        try:
            # load carga y valida los datos (lat, lon, fecha, nombre)
            estacion = estacion_schema.load(data, session=db.session)
        except ValidationError as err:
            return {"errors": err.messages}, 422

        db.session.add(estacion)
        db.session.commit()
        return estacion_schema.dump(estacion), 201


class EstacionDetail(Resource):
    # GET /api/estaciones/<id>
    def get(self, id):
        estacion = Estacion.query.get_or_404(id)
        return estacion_schema.dump(estacion), 200

    # PUT /api/estaciones/<id>
    def put(self, id):
        estacion = Estacion.query.get_or_404(id)
        data = request.get_json()
        if not data:
            return {"message": "Cuerpo JSON requerido."}, 400
        try:
            # actualizamos la instancia existente
            estacion = estacion_schema.load(data, instance=estacion, partial=False)
        except ValidationError as err:
            return {"errors": err.messages}, 422

        db.session.commit()
        return estacion_schema.dump(estacion), 200

    # DELETE /api/estaciones/<id>
    def delete(self, id):
        estacion = Estacion.query.get_or_404(id)
        db.session.delete(estacion)
        db.session.commit()
        return {"message": "Estación eliminada correctamente"}, 200


# Registro de rutas en el Api del blueprint
# OJO: Aquí se definen las URL finales
api.add_resource(EstacionList, "/estaciones", endpoint="estaciones")
api.add_resource(EstacionDetail, "/estaciones/<int:id>", endpoint="estacion_detail")