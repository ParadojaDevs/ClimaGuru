import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

export default function ListadoEstaciones() {
  const [estaciones, setEstaciones] = useState([]);
  const [cargando, setCargando] = useState(true);

  // 1. URL de tu Backend (Flask)
  const URL_BASE = "http://localhost:8080/api/estaciones";

  // 2. Cargar las estaciones al iniciar el componente
  useEffect(() => {
    cargarEstaciones();
  }, []);

  const cargarEstaciones = async () => {
    try {
      const respuesta = await fetch(URL_BASE);
      const datos = await respuesta.json();
      setEstaciones(datos);
      setCargando(false);
    } catch (error) {
      console.error("Error cargando estaciones:", error);
      setCargando(false);
    }
  };

  // 3. Función para Eliminar
  const eliminarEstacion = async (id) => {
    // A. Confirmación visual
    const confirmar = window.confirm("¿Estás seguro de que deseas eliminar esta estación? Esta acción no se puede deshacer.");

    if (confirmar) {
      try {
        // B. Petición DELETE al Backend
        const respuesta = await fetch(`${URL_BASE}/${id}`, {
          method: 'DELETE',
        });

        if (respuesta.ok) {
          // C. Si se borró bien en BD, actualizamos la lista visualmente
          // (Filtramos el array para quitar el que acabamos de borrar)
          setEstaciones(estaciones.filter((estacion) => estacion.id !== id));
        } else {
          alert("Error al intentar eliminar en el servidor.");
        }
      } catch (error) {
        console.error("Error de red:", error);
        alert("No se pudo conectar con el servidor.");
      }
    }
  };

  if (cargando) {
    return (
      <div className="container text-center mt-5">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Cargando...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container mt-5">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Listado de Estaciones Climáticas</h2>
        {/* Botón para ir a crear una nueva */}
        <Link to="/agregar" className="btn btn-primary">
          + Agregar Estación
        </Link>
      </div>

      <div className="table-responsive shadow-sm rounded">
        <table className="table table-striped table-hover align-middle">
          <thead className="table-dark">
            <tr>
              <th scope="col">ID</th>
              <th scope="col">Nombre</th>
              <th scope="col">Fecha (D/M/A)</th>
              <th scope="col">Latitud</th>
              <th scope="col">Longitud</th>
              <th scope="col" className="text-center">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {estaciones.length > 0 ? (
              estaciones.map((estacion) => (
                <tr key={estacion.id}>
                  <td>{estacion.id}</td>
                  <td className="fw-bold">{estacion.nombre}</td>
                  <td>
                    {estacion.dia}/{estacion.mes}/{estacion.anio}
                  </td>
                  <td>{estacion.latitud}</td>
                  <td>{estacion.longitud}</td>
                  <td className="text-center">
                    <div className="btn-group" role="group">
                      {/* Botón Ver Clima */}
                      <Link
                        to={`/clima/${estacion.id}`}
                        className="btn btn-info btn-sm me-2 text-white"
                        title="Ver Clima Actual"
                      >
                        🌥️ Clima
                      </Link>

                      {/* Botón Editar */}
                      <Link
                        to={`/editar/${estacion.id}`}
                        className="btn btn-warning btn-sm me-2"
                      >
                        Editar
                      </Link>

                      {/* Botón Eliminar */}
                      <button
                        onClick={() => eliminarEstacion(estacion.id)}
                        className="btn btn-danger btn-sm"
                      >
                        Eliminar
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="6" className="text-center py-4">
                  No hay estaciones registradas.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}