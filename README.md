# Clash Royale Analytics & Tactical Engine (v2.0)

Sistema cuantitativo de físicas, simulador predictivo de cambios de balance y analizador táctico de partidas (*Game Review*) para Clash Royale.

---

## 🏛️ Arquitectura del Proyecto



---

## 🚀 Inicio Rápido

### 1. Instalación de Dependencias

*(Requiere , ,  y ).*

### 2. Ejecutar la Demostración Local


### 3. Auditar Partidas del Top Ladder en Lote


### 4. Ejecutar la Suite de Pruebas Completa (13 pruebas)


---

## 🌐 Levantando el Servidor de la API (FastAPI)

Para iniciar el backend localmente y habilitar el consumo desde apps móviles (React Native/Expo) o dashboards web:



### 📖 Documentación Interactiva Swagger UI
Una vez arrancado el servidor, abre tu navegador en:
* **Swagger UI interactivo**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc alternativo**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📡 Endpoints de la API

### 1. Game Review de Partidas ()
Envía el historial de eventos de una partida y recibe:
* Puntuación de Precisión Táctica ().
* Detalle de **Trade Blunders** (jugadas que perdieron valor relativo frente a la mano disponible).
* Detalle de **Placement Blunders** (estructuras colocadas fuera del  de .5$ casillas).
* Detalle de **Fugas de Elixir** (segundos al tope de 10 de elixir).

### 2. Simulación de Parche de Balance ()
Envía un diccionario de 6 a 12 modificaciones simultáneas:

Y recibe el desplazamiento ponderado de elixir para cada carta, identificando a los ganadores directos y al **daño/beneficio colateral**.

### 3. Radar de Salud del Metajuego ()
Audita el metajuego en vivo y clasifica las cartas mediante hBcscore:
*  / 
* 
*  / 
Con sugerencias automáticas de ajuste acotadas por puntos de quiebre (*Hard Breakpoints*).

### 4. Fichas Técnicas e Interacciones de Hechizos ()
Devuelve las estadísticas exactas a Nivel 11 de torneo y su veredicto de supervivencia frente a los hechizos del juego (ej. Bola de Fuego, Tronco, Rayo).
