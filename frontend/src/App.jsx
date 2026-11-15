import { BrowserRouter, Route, Routes } from "react-router-dom";

import PublicMap from "./pages/PublicMap";
import LoginScreen from "./pages/LoginScreen";
import Dashboard from "./pages/Dashboard";

// Ruteo:
// - "/"        Mapa meteorologico publico (sin autenticacion)
// - "/login"   Acceso a la estacion (JWT existente)
// - "/dashboard" CRUD de usuarios (requiere token; redirige a /login)
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<PublicMap />} />
        <Route path="/login" element={<LoginScreen />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="*" element={<PublicMap />} />
      </Routes>
    </BrowserRouter>
  );
}
