import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navegacion from './Navegacion.jsx'
import ListadoEstaciones from './estaciones/ListadoEstaciones.jsx'
import AgregarEstacion from './estaciones/AgregarEstacion.jsx'
import EditarEstacion from './estaciones/EditarEstacion.jsx'
import ClimaDetalle from './estaciones/ClimaDetalle.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <Navegacion />

      <div className="container pb-4">
        <Routes>
          {/* Ruta Principal: Listado */}
          <Route path="/" element={<ListadoEstaciones />} />

          {/* Ruta Crear */}
          <Route path="/agregar" element={<AgregarEstacion />} />

          {/* Ruta Editar: Fíjate que usamos ":id" para coincidir con el useParams */}
          <Route path="/editar/:id" element={<EditarEstacion />} />
        </Routes>
      </div>

    </BrowserRouter>
  )
}