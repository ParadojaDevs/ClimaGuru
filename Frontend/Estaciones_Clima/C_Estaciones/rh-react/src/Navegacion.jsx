import { Link } from 'react-router-dom'

export default function Navegacion() {
  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
      <div className="container">
        {/* Marca / Logo */}
        <Link className="navbar-brand" to="/">Clima App</Link>

        <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navMain">
          <span className="navbar-toggler-icon"></span>
        </button>

        <div id="navMain" className="collapse navbar-collapse">
          <ul className="navbar-nav me-auto">
            <li className="nav-item">
              <Link className="nav-link" to="/">Estaciones</Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/agregar">Agregar Estación</Link>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  )
}
