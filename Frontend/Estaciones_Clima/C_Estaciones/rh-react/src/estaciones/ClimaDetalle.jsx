import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';

export default function ClimaDetalle() {
    const { id } = useParams();
    const [clima, setClima] = useState(null);
    const [cargando, setCargando] = useState(true);
    const [error, setError] = useState(null);

    const URL_CLIMA = `http://localhost:8080/api/clima/${id}`;

    useEffect(() => {
        fetch(URL_CLIMA)
            .then((res) => {
                if (!res.ok) throw new Error("No se pudo obtener el clima");
                return res.json();
            })
            .then((data) => {
                setClima(data);
                setCargando(false);
            })
            .catch((err) => {
                console.error("Error:", err);
                setError("Error al cargar datos del clima. Verifica que la API Key esté configurada.");
                setCargando(false);
            });
    }, [id]);

    if (cargando) {
        return (
            <div className="container text-center mt-5">
                <div className="spinner-border text-primary" role="status">
                    <span className="visually-hidden">Cargando...</span>
                </div>
                <p className="mt-2">Consultando APIs satelitales...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="container mt-5">
                <div className="alert alert-danger">{error}</div>
                <Link to="/" className="btn btn-secondary">Volver</Link>
            </div>
        );
    }

    return (
        <div className="container mt-5">
            <div className="card shadow-lg">
                <div className="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                    <h2 className="mb-0">Reporte Climático</h2>
                    <Link to="/" className="btn btn-outline-light btn-sm">Volver al Listado</Link>
                </div>

                <div className="card-body">
                    {/* Si la respuesta es de OpenWeather (tiene 'current') */}
                    {clima.current && (
                        <div className="row text-center">
                            <div className="col-md-4 mb-3">
                                <div className="p-3 border rounded bg-light">
                                    <h4>Temperatura</h4>
                                    <p className="display-4">{Math.round(clima.current.main.temp - 273.15)}°C</p>
                                    <small className="text-muted">Sensación: {Math.round(clima.current.main.feels_like - 273.15)}°C</small>
                                </div>
                            </div>
                            <div className="col-md-4 mb-3">
                                <div className="p-3 border rounded bg-light">
                                    <h4>Humedad</h4>
                                    <p className="display-4">{clima.current.main.humidity}%</p>
                                </div>
                            </div>
                            <div className="col-md-4 mb-3">
                                <div className="p-3 border rounded bg-light">
                                    <h4>Condición</h4>
                                    <p className="display-4 text-capitalize">{clima.current.weather[0].description}</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Si la respuesta es de Open-Meteo (tiene 'current_weather') */}
                    {clima.current_weather && (
                        <div className="row text-center">
                            <div className="col-md-4 mb-3">
                                <div className="p-3 border rounded bg-light">
                                    <h4>Temperatura</h4>
                                    <p className="display-4">{clima.current_weather.temperature}°C</p>
                                </div>
                            </div>
                            <div className="col-md-4 mb-3">
                                <div className="p-3 border rounded bg-light">
                                    <h4>Viento</h4>
                                    <p className="display-4">{clima.current_weather.windspeed} km/h</p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Raw Data para depuración o si es otro formato */}
                    <div className="mt-4">
                        <details>
                            <summary className="text-muted">Ver datos crudos (JSON)</summary>
                            <pre className="bg-dark text-light p-3 rounded mt-2">
                                {JSON.stringify(clima, null, 2)}
                            </pre>
                        </details>
                    </div>

                </div>
            </div>
        </div>
    );
}
