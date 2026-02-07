import { useState } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
// Asegúrate de que la ruta a tu config sea correcta
import { urlBase } from '../config' 

export default function AgregarEstacion() {
  
  // 1. Definimos el estado inicial del formulario
  const [estacion, setEstacion] = useState({
    nombre: '',
    dia: '',
    mes: '',
    anio: '',
    latitud: '',
    longitud: ''
  })

  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')
  
  const navigate = useNavigate()

  // 2. Manejar cambios en los inputs
  const onInputChange = (e) => {
    setEstacion({ ...estacion, [e.target.name]: e.target.value })
  }

  // 3. Enviar el formulario (Submit)
  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')

    // Validación simple
    if (!estacion.nombre || !estacion.latitud || !estacion.longitud) {
        setError('Por favor completa los campos obligatorios.')
        return
    }

    try {
      setEnviando(true)
      // Enviamos los datos al backend con POST
      await axios.post(urlBase, estacion)
      
      // Redirigimos al inicio después de guardar
      navigate('/') 
    } catch (e) {
      console.error(e)
      setError('Ocurrió un error al guardar la estación.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="container mt-5">
      <div className="card">
        <div className="card-header">
          <strong>Agregar Nueva Estación</strong>
        </div>
        <div className="card-body">
            
          {error && <div className="alert alert-danger">{error}</div>}

          <form onSubmit={onSubmit}>
            
            {/* Nombre */}
            <div className="mb-3">
              <label className="form-label">Nombre de la Estación</label>
              <input
                type="text"
                className="form-control"
                name="nombre"
                value={estacion.nombre}
                onChange={onInputChange}
                placeholder="Ej. Torre SIATA"
                required
              />
            </div>

            {/* Fecha (Agrupada) */}
            <div className="row mb-3">
                <div className="col">
                    <label className="form-label">Día</label>
                    <input 
                        type="number" className="form-control" name="dia" 
                        value={estacion.dia} onChange={onInputChange} placeholder="DD" 
                    />
                </div>
                <div className="col">
                    <label className="form-label">Mes</label>
                    <input 
                        type="number" className="form-control" name="mes" 
                        value={estacion.mes} onChange={onInputChange} placeholder="MM" 
                    />
                </div>
                <div className="col">
                    <label className="form-label">Año</label>
                    <input 
                        type="number" className="form-control" name="anio" 
                        value={estacion.anio} onChange={onInputChange} placeholder="AAAA" 
                    />
                </div>
            </div>

            {/* Ubicación */}
            <div className="row mb-3">
                <div className="col">
                    <label className="form-label">Latitud</label>
                    <input
                        type="number"
                        step="any" // Permite decimales
                        className="form-control"
                        name="latitud"
                        value={estacion.latitud}
                        onChange={onInputChange}
                        placeholder="Ej. 6.259"
                        required
                    />
                </div>
                <div className="col">
                    <label className="form-label">Longitud</label>
                    <input
                        type="number"
                        step="any" // Permite decimales y negativos
                        className="form-control"
                        name="longitud"
                        value={estacion.longitud}
                        onChange={onInputChange}
                        placeholder="Ej. -75.591"
                        required
                    />
                </div>
            </div>

            {/* Botones */}
            <div className="d-grid gap-2">
                <button type="submit" className="btn btn-primary" disabled={enviando}>
                  {enviando ? 'Guardando...' : 'Agregar Estación'}
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => navigate('/')}>
                  Cancelar
                </button>
            </div>

          </form>
        </div>
      </div>
    </div>
  )
}