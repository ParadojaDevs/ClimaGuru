// URL del backend para las Estaciones del Clima
// Respuesta esperada (JSON):
// [
//   { 
//     "id": 1, 
//     "nombre": "Torre SIATA", 
//     "dia": 12, 
//     "mes": 5, 
//     "anio": 2024, 
//     "latitud": 6.259, 
//     "longitud": -75.591 
//   },
//   ...
// ]

// Asegúrate de que tu backend tenga este endpoint habilitado:
export const urlBase = 'http://localhost:8080/api/estaciones'