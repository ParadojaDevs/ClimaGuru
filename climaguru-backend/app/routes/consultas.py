# Realizar consultas meteorológicas
"""
Rutas de Consultas
==================
Endpoints para realizar consultas meteorológicas
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.extensions import db
from app.models.consulta import Consulta
from app.models.dato_meteorologico import DatosClima
from app.models.logs_actividad import LogsActividad

consultas_bp = Blueprint('consultas', __name__)


@consultas_bp.route('/tiempo-real', methods=['POST'])
@jwt_required()
def consulta_tiempo_real():
    """
    Realizar consulta de clima en tiempo real
    
    Body JSON:
        - ciudad: string (opcional si se envían coordenadas)
        - latitud: float (opcional si se envía ciudad)
        - longitud: float (opcional si se envía ciudad)
        - parametros: array de strings (temperatura, presion, viento, etc.)
        - formato: string (json, csv, txt, yaml) - default: json
    
    Returns:
        - consulta: datos de la consulta registrada
        - datos: datos climáticos procesados
    """
    usuario_id = get_jwt_identity()
    data = request.get_json()
    
    # Validar que tenga ciudad o coordenadas
    if not data.get('ciudad') and (not data.get('latitud') or not data.get('longitud')):
        return jsonify({
            'error': 'Debe proporcionar ciudad o coordenadas (latitud, longitud)'
        }), 400
    
    # Crear registro de consulta
    consulta = Consulta(
        usuario_id=usuario_id,
        tipo_consulta='tiempo_real',
        ciudad=data.get('ciudad'),
        latitud=data.get('latitud'),
        longitud=data.get('longitud'),
        formato_salida=data.get('formato', 'json'),
        parametros_solicitados=data.get('parametros', ['temperatura', 'humedad', 'viento']),
        estado='procesando',
        ip_origen=request.remote_addr
    )
    
    db.session.add(consulta)
    db.session.commit()
    
    # TODO: Aquí se integrarían los clientes de las APIs externas
    # Por ahora, simulamos una respuesta
    
    try:
        # Simular consulta a APIs externas
        # En producción: climapi = ClimaAPIManager()
        # datos = climapi.get_current_weather(lat, lon)
        
        datos_simulados = {
            'temperatura': 24.5,
            'humedad': 65,
            'presion': 1013,
            'viento_velocidad': 12,
            'viento_direccion': 180,
            'descripcion': 'Parcialmente nublado'
        }
        
        # Guardar datos procesados
        datos_clima = DatosClima(
            consulta_id=consulta.id,
            temperatura_promedio=datos_simulados['temperatura'],
            humedad_relativa=datos_simulados['humedad'],
            presion_atmosferica=datos_simulados['presion'],
            velocidad_viento=datos_simulados['viento_velocidad'],
            direccion_viento=datos_simulados['viento_direccion'],
            descripcion_clima=datos_simulados['descripcion'],
            fuentes_utilizadas=['openweather', 'openmeteo'],
            datos_completos=datos_simulados
        )
        
        db.session.add(datos_clima)
        
        # Actualizar consulta
        consulta.estado = 'completada'
        consulta.completada_en = datetime.utcnow()
        consulta.tiempo_respuesta_ms = 500  # Simulado
        
        db.session.commit()
        
        # Registrar log
        log = LogActividad(
            usuario_id=usuario_id,
            accion='consulta_tiempo_real',
            detalle={
                'consulta_id': consulta.id,
                'ciudad': consulta.ciudad,
                'coordenadas': f"{consulta.latitud}, {consulta.longitud}"
            },
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'consulta': consulta.to_dict(),
            'datos': datos_clima.to_dict()
        }), 200
        
    except Exception as e:
        consulta.estado = 'error'
        consulta.mensaje_error = str(e)
        db.session.commit()
        
        return jsonify({
            'error': 'Error al procesar la consulta',
            'message': str(e)
        }), 500


@consultas_bp.route('/historico', methods=['POST'])
@jwt_required()
def consulta_historico():
    """
    Realizar consulta de datos históricos
    
    Body JSON:
        - ciudad: string (opcional si se envían coordenadas)
        - latitud: float (opcional si se envía ciudad)
        - longitud: float (opcional si se envía ciudad)
        - fecha_inicio: string (YYYY-MM-DD)
        - fecha_fin: string (YYYY-MM-DD)
        - parametros: array de strings
        - formato: string (json, csv, txt, yaml)
    
    Returns:
        - consulta: datos de la consulta
        - datos: datos históricos procesados
    """
    usuario_id = get_jwt_identity()
    data = request.get_json()
    
    # Validaciones
    if not data.get('ciudad') and (not data.get('latitud') or not data.get('longitud')):
        return jsonify({
            'error': 'Debe proporcionar ciudad o coordenadas'
        }), 400
    
    if not data.get('fecha_inicio') or not data.get('fecha_fin'):
        return jsonify({
            'error': 'Debe proporcionar fecha_inicio y fecha_fin'
        }), 400
    
    # Crear consulta
    consulta = Consulta(
        usuario_id=usuario_id,
        tipo_consulta='historico',
        ciudad=data.get('ciudad'),
        latitud=data.get('latitud'),
        longitud=data.get('longitud'),
        fecha_inicio=data.get('fecha_inicio'),
        fecha_fin=data.get('fecha_fin'),
        formato_salida=data.get('formato', 'json'),
        parametros_solicitados=data.get('parametros'),
        estado='procesando',
        ip_origen=request.remote_addr
    )
    
    db.session.add(consulta)
    db.session.commit()
    
    # TODO: Integrar con APIs históricas
    # Por ahora, simulamos
    
    consulta.estado = 'completada'
    consulta.completada_en = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'message': 'Consulta histórica registrada',
        'consulta': consulta.to_dict()
    }), 200


@consultas_bp.route('/mis-consultas', methods=['GET'])
@jwt_required()
def get_mis_consultas():
    """
    Obtener historial de consultas del usuario
    
    Query params:
        - page: int (default: 1)
        - per_page: int (default: 10, max: 100)
        - tipo: string (tiempo_real, historico)
        - estado: string (pendiente, procesando, completada, error)
    
    Returns:
        - consultas: lista de consultas
        - total: total de consultas
        - pages: total de páginas
    """
    usuario_id = get_jwt_identity()
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    tipo = request.args.get('tipo')
    estado = request.args.get('estado')
    
    query = Consulta.query.filter_by(usuario_id=usuario_id)
    
    if tipo:
        query = query.filter_by(tipo_consulta=tipo)
    if estado:
        query = query.filter_by(estado=estado)
    
    pagination = query.order_by(Consulta.creada_en.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'consultas': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page
    }), 200


@consultas_bp.route('/<int:consulta_id>', methods=['GET'])
@jwt_required()
def get_consulta(consulta_id):
    """
    Obtener detalle de una consulta específica
    
    Args:
        consulta_id: ID de la consulta
    
    Returns:
        - consulta: datos de la consulta
        - datos_clima: datos climáticos asociados (si existen)
    """
    usuario_id = get_jwt_identity()
    
    consulta = Consulta.query.filter_by(id=consulta_id, usuario_id=usuario_id).first()
    
    if not consulta:
        return jsonify({'error': 'Consulta no encontrada'}), 404
    
    response = {'consulta': consulta.to_dict()}
    
    if consulta.datos_clima:
        response['datos_clima'] = consulta.datos_clima.to_dict()
    
    return jsonify(response), 200


@consultas_bp.route('/<int:consulta_id>/descargar', methods=['GET'])
@jwt_required()
def descargar_consulta(consulta_id):
    """
    Descargar datos de una consulta en el formato solicitado
    
    Args:
        consulta_id: ID de la consulta
    
    Returns:
        - Archivo en formato JSON, CSV, TXT o YAML
    """
    usuario_id = get_jwt_identity()
    
    consulta = Consulta.query.filter_by(id=consulta_id, usuario_id=usuario_id).first()
    
    if not consulta:
        return jsonify({'error': 'Consulta no encontrada'}), 404
    
    if consulta.estado != 'completada':
        return jsonify({'error': 'La consulta no está completada'}), 400
    
    if not consulta.datos_clima:
        return jsonify({'error': 'No hay datos disponibles'}), 404
    
    formato = consulta.formato_salida
    datos = consulta.datos_clima.to_dict()
    
    if formato == 'json':
        return jsonify(datos), 200
    
    elif formato == 'csv':
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        writer.writerow(['Parametro', 'Valor'])
        
        # Escribir datos
        writer.writerow(['Temperatura Promedio', datos['temperatura']['promedio']])
        writer.writerow(['Temperatura Min', datos['temperatura']['min']])
        writer.writerow(['Temperatura Max', datos['temperatura']['max']])
        writer.writerow(['Presion', datos['presion_atmosferica']])
        writer.writerow(['Humedad', datos['humedad_relativa']])
        writer.writerow(['Viento Velocidad', datos['viento']['velocidad']])
        writer.writerow(['Viento Direccion', datos['viento']['direccion']])
        
        output.seek(0)
        
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename=consulta_{consulta_id}.csv'
        }
    
    elif formato == 'txt':
        texto = f"""
CONSULTA CLIMÁTICA - ClimaGuru
==============================
ID Consulta: {consulta_id}
Fecha: {consulta.creada_en}

DATOS OBTENIDOS:
----------------
Temperatura: {datos['temperatura']['promedio']}°C
  - Mínima: {datos['temperatura']['min']}°C
  - Máxima: {datos['temperatura']['max']}°C
Presión Atmosférica: {datos['presion_atmosferica']} hPa
Humedad: {datos['humedad_relativa']}%
Viento: {datos['viento']['velocidad']} km/h, dirección {datos['viento']['direccion']}°
Descripción: {datos['descripcion_clima']}

Fuentes: {', '.join(datos['fuentes_utilizadas'] or [])}
"""
        return texto, 200, {'Content-Type': 'text/plain'}
    
    elif formato == 'yaml':
        try:
            import yaml
            return yaml.dump(datos), 200, {'Content-Type': 'text/yaml'}
        except ImportError:
            return jsonify({'error': 'Formato YAML no disponible'}), 500
    
    return jsonify({'error': 'Formato no soportado'}), 400
