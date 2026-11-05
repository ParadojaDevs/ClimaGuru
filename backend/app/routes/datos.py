# Obtener datos históricos y estadísticas
"""
Rutas de Datos
================
Endpoints para obtener datos históricos y estadísticas
"""
from flask import Blueprint, jsonify

datos_bp = Blueprint('datos', __name__)

@datos_bp.route('/historicos', methods=['GET'])
def get_historicos():
    """Obtener datos históricos"""
    return jsonify({'message': 'Endpoint de datos históricos'})
