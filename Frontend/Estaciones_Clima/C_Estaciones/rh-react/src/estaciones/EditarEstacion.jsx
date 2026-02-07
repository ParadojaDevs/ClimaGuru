import { useEffect, useState } from 'react'
import axios from 'axios'
import { NumericFormat } from 'react-number-format'
import { useNavigate, useParams } from 'react-router-dom'
import { urlBase } from '../config'

export default function EditarEstacion() {
  // Asumimos que en tu ruta definiste el param como ":id"
  const { id } = useParams() 
  const navigate = useNavigate()

  const [nombre, setNombre] = useState('')
  const [dia, setDia] = useState('')
  const [mes, setMes] = useState('')
  const [anio, setAnio] = useState('')
  const [latitud, setLatitud] = useState('')
  const [longitud, setLongitud] = useState('')

  const [cargando, setCargando] = useState(true)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const cargar = async () => {
      try {
        const { data } = await axios.get(`${urlBase}/${id}`)
        // Llenamos los estados con la info que viene de la BD
        setNombre(data?.nombre ?? '')
        setDia(data?.dia ?? '')
        setMes(data?.mes ?? '')
        setAnio(data?.anio ?? '')
        setLatitud(data?.latitud ?? '')
        setLongitud(data?.longitud ?? '')
      } catch (e) {
        setError('No se pudo cargar la información de la estación.')
      } finally {
        setCargando(false)
      }
    }
    cargar()
  }, [id])

  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')

    const nombreOk = nombre.trim()
    const d = Number(dia)
    const m = Number(mes)
    const a = Number(anio)
    const lat = Number(latitud)
    const lon = Number(longitud)

    // Validación básica: nombre y que las coordenadas no sean nulas/cero si son obligatorias
    if (!nombreOk || !d || !m || !a || lat === 0 || lon === 0) {
      setError('Por favor verifica que todos los datos sean correctos.')
      return
    }

    try {
      setEnviando(true)
      await axios.put(`${urlBase}/${id}`, {
        nombre: nombreOk,
        dia: d,
        mes: m,
        anio: a,
        latitud: lat,
        longitud: lon
      })
      navigate('/')
    } catch (e) {
      setError('No se pudo actualizar la estación.')
    } finally {
      setEnviando(false)
    }
  }

  if (cargando) return <div className="container mt-4"><p>Cargando datos...</p></div>

  return (
    <div className="container mt-5">
      <div className="card">
        <div className="card-header">
          <strong>Editar Estación #{id}</strong>
        </div>
        <div className="card-body">
          {error && <div className="alert alert-danger mb-3">{error}</div>}

          <form onSubmit={onSubmit}>
            
            {/* Nombre */}
            <div className="mb-3">
              <label className="form-label">Nombre</label>
              <input
                className="form-control"
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
                placeholder="Nombre de la estación"
              />
            </div>

            {/* Fecha (3 columnas) */}
            <div className="row mb-3">
              <div className="col-md-4">
                <label className="form-label">Día</label>
                <input
                  type="number"
                  className="form-control"
                  value={dia}
                  onChange={(e) => setDia(e.target.value)}
                />
              </div>
              <div className="col-md-4">
                <label className="form-label">Mes</label>
                <input
                  type="number"
                  className="form-control"
                  value={mes}
                  onChange={(e) => setMes(e.target.value)}
                />
              </div>
              <div className="col-md-4">
                <label className="form-label">Año</label>
                <input
                  type="number"
                  className="form-control"
                  value={anio}
                  onChange={(e) => setAnio(e.target.value)}
                />
              </div>
            </div>

            {/* Coordenadas (2 columnas) */}
            <div className="row mb-3">
              <div className="col-md-6">
                <label className="form-label">Latitud</label>
                <NumericFormat
                  className="form-control"
                  value={latitud}
                  thousandSeparator={false}
                  decimalSeparator="."
                  decimalScale={6}
                  allowNegative={true}
                  placeholder="Ej. 6.259"
                  onValueChange={({ floatValue }) => setLatitud(floatValue ?? '')}
                />
              </div>
              <div className="col-md-6">
                <label className="form-label">Longitud</label>
                <NumericFormat
                  className="form-control"
                  value={longitud}
                  thousandSeparator={false}
                  decimalSeparator="."
                  decimalScale={6}
                  allowNegative={true}
                  placeholder="Ej. -75.591"
                  onValueChange={({ floatValue }) => setLongitud(floatValue ?? '')}
                />
              </div>
            </div>

            {/* Botones */}
            <div className="col-12 d-flex gap-2">
              <button type="submit" className="btn btn-primary" disabled={enviando}>
                {enviando ? 'Guardando…' : 'Guardar Cambios'}
              </button>
              <button type="button" className="btn btn-secondary" onClick={() => navigate(-1)}>
                Cancelar
              </button>
            </div>

          </form>
        </div>
      </div>
    </div>
  )
}