"""Rutas para ingesta de datos meteorologicos.

Endpoints para ejecutar ingesta desde fuentes externas
(IDEAM radar y SAB lluvias).
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.services.weather_service import weather_service
from app.models.logs_actividad import LogsActividad
from app.extensions import db

ingestion_bp = Blueprint('ingestion', __name__)


@ingestion_bp.route('/sources', methods=['GET'])
def get_sources():
    """Obtener fuentes de datos disponibles."""
    try:
        info = weather_service.get_sources_info()
        return jsonify(info), 200
    except Exception as e:
        return jsonify({
            'error': 'Error al obtener fuentes',
            'message': str(e)
        }), 500


@ingestion_bp.route('/sab', methods=['POST'])
@jwt_required()
def ingest_sab():
    """
    Ingestar datos desde SAB (Sistema de Alerta de Bogota).

    Returns:
        Resumen de ingesta
    """
    usuario_id = get_jwt_identity()

    try:
        result = weather_service.ingest_data('sab_lluvias')
        if result['status'] == 'success':
            log = LogsActividad(
                usuario_id=usuario_id,
                accion='ingestion_sab',
                detalle=result,
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
        return jsonify(result), 200 if result['status'] == 'success' else 500
    except Exception as e:
        return jsonify({
            'error': 'Error en ingesta SAB',
            'message': str(e)
        }), 500


@ingestion_bp.route('/ideam', methods=['POST'])
@jwt_required()
def ingest_ideam():
    """
    Ingestar datos desde IDEAM radar.

    Body JSON (opcional):
        - radar: nombre del radar
        - fecha: fecha para busqueda
        - limite: numero maximo de archivos

    Returns:
        Resumen de ingesta
    """
    usuario_id = get_jwt_identity()
    data = request.get_json() or {}

    try:
        result = weather_service.ingest_data('ideam_radar', **data)
        if result['status'] == 'success':
            log = LogsActividad(
                usuario_id=usuario_id,
                accion='ingestion_ideam',
                detalle=result,
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
        return jsonify(result), 200 if result['status'] == 'success' else 500
    except Exception as e:
        return jsonify({
            'error': 'Error en ingesta IDEAM',
            'message': str(e)
        }), 500


@ingestion_bp.route('/all', methods=['POST'])
@jwt_required()
def ingest_all():
    """
    Ingestar datos desde todas las fuentes disponibles.

    Returns:
        Resultados por fuente
    """
    usuario_id = get_jwt_identity()
    data = request.get_json() or {}

    try:
        results = weather_service.ingest_all_sources(**data)
        log = LogsActividad(
            usuario_id=usuario_id,
            accion='ingestion_all',
            detalle={'results': results},
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        return jsonify({'results': results}), 200
    except Exception as e:
        return jsonify({
            'error': 'Error en ingesta multiple',
            'message': str(e)
        }), 500


@ingestion_bp.route('/observations', methods=['GET'])
def get_observations():
    """
    Obtener observaciones meteorologicas normalizadas.

    Query params:
        - fuente: ideam_radar | sab_lluvias
        - tipo_dato: tipo de dato a filtrar
        - limit: numero maximo (default 100)

    Returns:
        Lista de observaciones
    """
    fuente = request.args.get('fuente')
    tipo_dato = request.args.get('tipo_dato')
    try:
        limit = int(request.args.get('limit', 100))
    except ValueError:
        limit = 100

    try:
        observations = weather_service.get_latest_observations(
            fuente=fuente,
            tipo_dato=tipo_dato,
            limit=limit
        )
        return jsonify({'observations': observations, 'count': len(observations)}), 200
    except Exception as e:
        return jsonify({
            'error': 'Error al obtener observaciones',
            'message': str(e)
        }), 500
