"""Spatial API routes."""
from flask import Blueprint, request, jsonify
from app.services.spatial_service import SpatialService

spatial_bp = Blueprint('spatial', __name__)
svc = SpatialService()


@spatial_bp.route('/observations/nearby', methods=['GET'])
def nearby():
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        radius_km = float(request.args.get('radius_km', 10))
        fuente = request.args.get('fuente')
        tipo_dato = request.args.get('tipo_dato')
        limit = int(request.args.get('limit', 100))
        obs = svc.find_nearby(lat, lon, radius_km, fuente, tipo_dato, limit)
        return jsonify({'observations': obs, 'count': len(obs)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@spatial_bp.route('/observations/bbox', methods=['GET'])
def bbox():
    try:
        min_lat = float(request.args.get('min_lat'))
        max_lat = float(request.args.get('max_lat'))
        min_lon = float(request.args.get('min_lon'))
        max_lon = float(request.args.get('max_lon'))
        fuente = request.args.get('fuente')
        tipo_dato = request.args.get('tipo_dato')
        limit = int(request.args.get('limit', 500))
        obs = svc.find_in_bbox(min_lat, max_lat, min_lon, max_lon, fuente, tipo_dato, limit)
        return jsonify({'observations': obs, 'count': len(obs)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@spatial_bp.route('/observations/geojson', methods=['GET'])
def geojson():
    try:
        fuente = request.args.get('fuente')
        tipo_dato = request.args.get('tipo_dato')
        limit = int(request.args.get('limit', 200))
        obs = svc.get_latest_observations(fuente, tipo_dato, limit)
        return jsonify(svc.to_geojson(obs)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@spatial_bp.route('/observations/tiles/info', methods=['GET'])
def tiles_info():
    return jsonify({
        'type': 'vector',
        'format': 'geojson',
        'description': 'Prepared for map visualization layers'
    }), 200
