from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.distance import great_circle
from osmnx.utils import log
from itertools import groupby
from isodate import parse_duration #para trabajar con fechas en formato ISO 8601
import requests #para trabajar con la API
import sys #para utilizar el max_int
import openrouteservice
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd



def calcular_tiempos(coord_origen, coord_destino):

    tiempo_coche = obtener_tiempo_viaje_openrouteservice(api_key_openrouteservice, coord_origen, coord_destino, perfil_coche) / 3600
    tiempo_bici = obtener_tiempo_viaje_openrouteservice(api_key_openrouteservice, coord_origen, coord_destino, perfil_bici) / 3600
    tiempo_pie = obtener_tiempo_viaje_openrouteservice(api_key_openrouteservice, coord_origen, coord_destino, perfil_pie) / 3600

    if tiempo_pie < 0.6:
        return tiempo_pie
    if tiempo_bici < 0.75:
        return tiempo_bici      
    else:
        return tiempo_coche


def calcular_ruta(origenes, destino, ciudades):
    mejores_rutas = []
    for i, (origen, coord_origen) in enumerate(zip(ciudades, origenes), start=1):
        aeropuerto = obtener_cordenadas_aeropuerto(coord_origen[1],coord_origen[0])
        distancia = geodesic(coord_origen, destino).kilometers
	
        # Suponiendo que las siguientes funciones están definidas y funcionando correctamente
        tiempo = calcular_tiempos(coord_origen, destino)
       

        ruta_info = {
            "Persona": f"Persona_{i}",
            "Origen": origen,
            "Destino": destino,
            "Distancia": distancia,
            "Tiempo": tiempo,
            "Aeropuerto": {
                "Nombre": aeropuerto['name'],
                "Latitud": aeropuerto['latitude_deg'],
                "Longitud": aeropuerto['longitude_deg']
            }
        }

        mejores_rutas.append(ruta_info)
    
    return mejores_rutas

def obtener_coordenadas(lugar):
    geolocalizador = Nominatim(user_agent="tu_aplicacion")
    ubicacion = geolocalizador.geocode(lugar)

    if ubicacion:
        return ubicacion.longitude, ubicacion.latitude
    else:
        print(f"No se pudo encontrar la ubicación de {lugar}")
        return None

def obtener_tiempo_viaje_openrouteservice(api_key, origen, destino, perfil):
    client = openrouteservice.Client(key=api_key)
    
    # Crear una solicitud de direcciones
    ruta = client.directions(
        coordinates=[origen, destino],
        profile=perfil,
        format='geojson',
        radiuses=[10000, 10000]
    )

    if ruta and 'features' in ruta:
        # Extraer la duración del viaje desde las propiedades de la ruta
        duracion = ruta['features'][0]['properties']['segments'][0]['duration']
        return duracion
    else:
        print(f"No se pudo obtener la duración del viaje entre {origen} y {destino} en modo {perfil}")
        return None
        
def find_nearest_public_airport(latitude, longitude, airports_data):
        min_distance = float('inf')
        nearest_airport = None

        # Filtrar aeropuertos por tipo de uso (público)
        public_airports = airports_data[airports_data['type'] == 'large_airport']
 
        for index, airport in public_airports.iterrows():
            airport_coord = (airport['latitude_deg'], airport['longitude_deg'])
            distance = great_circle((latitude, longitude), airport_coord).kilometers
            if distance < min_distance:
                 min_distance = distance
                 nearest_airport = airport
        return nearest_airport

def obtener_cordenadas_aeropuerto(latitude, longitude):
    # Cargar datos de aeropuertos desde un archivo CSV, puedes encontrar estos datos en OurAirports.
    airports_data = pd.read_csv('airports.csv')
    
    # Se optiene el aeropuerto mas cercano para las posiciones dadas
    nearest_airport = find_nearest_public_airport(latitude, longitude, airports_data)  # Usar la función correcta
    
    # Si se encuenta se devuelve la posicion del aeropuerto mas cercano
    if nearest_airport is not None:
        return nearest_airport
    else:
        print("No se encontró ningún aeropuerto cercano.")
        return None

def eliminar_y_mostrar_info(sublistas_filtradas):
    personas_aeropuerto_solo = {}  # Diccionario para almacenar la información de las personas que van al aeropuerto solas
    personas_aeropuerto_compartido = []  # Lista para almacenar las rutas de personas que van al aeropuerto compartiendo coche
    
    for sublista in sublistas_filtradas:
        rutas_no_aeropuerto = []  # Lista para almacenar las rutas de personas que no van al aeropuerto
        
        for ruta in sublista:
            # Comprobar si la distancia al aeropuerto es menor que la distancia al destino
            distancia_a_aeropuerto = calcular_distancia((ruta['Destino'][1], ruta['Destino'][0]), (ruta['Aeropuerto']['Latitud'], ruta['Aeropuerto']['Longitud']))
            if distancia_a_aeropuerto < ruta['Distancia']:
                # Guardar información de persona y aeropuerto si cumple la condición
                personas_aeropuerto_solo[ruta['Persona']] = ruta['Aeropuerto']['Nombre']
            else:
                # Guardar información de persona si no cumple la condición
                rutas_no_aeropuerto.append(ruta)
                personas_aeropuerto_compartido.append(ruta['Persona'])
        
        # Reemplazar la lista original por la lista de rutas que no van al aeropuerto
        sublista[:] = rutas_no_aeropuerto

    # Imprimir las personas que van al aeropuerto solas
    print("Personas que van en coche solo al aeropuerto:")
    for persona, aeropuerto in personas_aeropuerto_solo.items():
        print(f"La Persona {persona} va en coche solo al {aeropuerto}.")

    # Imprimir las personas que van al aeropuerto compartiendo coche
    print("Personas que van en coche compartido al aeropuerto:")
    for persona in personas_aeropuerto_compartido:
        print(f"La Persona {persona} va en coche compartido al {aeropuerto}.")    
       
###################### CODE FOR API ###################################
    
# struct para alamcenar algunos datos sobre el vuelo mas optimo
class FlightStruct:
    def __init__(self, departure_location, arrival_location, duration, num_escalas):
        self.departure_location = departure_location
        self.arrival_location = arrival_location
        self.duration = duration
        self.num_escalas = num_escalas


#para transformar el fomato de fecha ISO 8601
def parse_duration_to_hours(duration):
    total_seconds = duration.total_seconds()
    total_hours = total_seconds / 3600
    return total_hours


#funcion Dios
def get_flight_inspiration(origin, destination):

    # URL de la API de Amadeus
    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    # credenciales de Amadeus
    api_key = "FAGguVy1irFqL6UN4VtG1tFphCZb"
    # parámetros de la solicitud (se predefine una fecha y numero de viajeros)
    params = {
        'originLocationCode': origin,
        'destinationLocationCode': destination,
        'departureDate': "2024-05-02",
        'adults': 1,
    }
    # se configuran las cabeceras con la clave de API
    headers = {
        'Authorization': f'Bearer {api_key}',
    }
    # se realiza la solicitud GET
    response = requests.get(url, params=params, headers=headers)

    # verificamos el estado de la respuesta
    if response.status_code == 200:
        # procesar la respuesta JSON
        data = response.json()
        # inicializamos los valores del struct
        struct_res = FlightStruct(origin, destination, sys.maxsize, sys.maxsize)
        # variables para la suma total de horas y minutos
        total_hours = 0
        # contador para limitar la impresión a 5 vuelos
        flight_count = 0
        # variable para contabilizar el numero de escalas
        escalas = -1

        # iteraramos sobre las ofertas de vuelos
        for offer in data.get('data', []):
            print(origin, " -> ", destination, "\n")
            # iteramos sobre los itinerarios
            for itinerary in offer.get('itineraries', []):
                for segment in itinerary.get('segments', []):
                    duration_str = segment.get('duration', '')
                    # parsear la duración a formato de timedelta
                    duration = parse_duration(duration_str)
                    total_hours += parse_duration_to_hours(duration)
                    # aumentar el numero de escalas
                    escalas+=1

                #para actualizar el struct dependiendo del vuelo mas optimo 
                if (escalas < struct_res.num_escalas):
                    struct_res.num_escalas = escalas
                    struct_res.duration = total_hours
                elif ((total_hours < struct_res.duration) & (escalas < struct_res.num_escalas)):
                    struct_res.num_escalas = escalas
                    struct_res.duration = total_hours
                else:
                    continue
            
            #reseteamos las variables
            total_hours = 0 
            escalas = 0

            # incrementar el contador
            flight_count += 1
            
            # salir del bucle después de imprimir 5 vuelos
            if flight_count >= 5:
                break
        

        return struct_res
    
    else:
        # manejar errores
        print(f"Error en la solicitud: {response.status_code}")
        print(response.text)    
    
def mejor_vuelo_para_destino(sublistas_filtradas, destino):
    print(f"\nMejores vuelos para llegar a {destino} desde los distintos aeropuertos:")

    for sublista in sublistas_filtradas:
        for ruta in sublista:
                   
            aeropuerto = obtener_cordenadas_aeropuerto(destino[0], destino[1])
            # Obtener la información del vuelo más óptimo desde el aeropuerto al destino
            vuelo_optimo = get_flight_inspiration(ruta['Aeropuerto']['Nombre'], destino)

            print(f"\nPara la Persona {ruta['Persona']} que va desde {ruta['Origen']} al aeropuerto {ruta['Aeropuerto']['Nombre']}:")

            # Imprimir la información del vuelo óptimo
            if vuelo_optimo and vuelo_optimo.duration != sys.maxsize:
                print(f"Duración del vuelo más óptimo: {vuelo_optimo.duration:.2f} horas")
                print(f"Número de escalas: {vuelo_optimo.num_escalas}")
            else:
                print("No se encontraron vuelos disponibles.")    
    
if __name__ == "__main__":

    api_key_openrouteservice = "5b3ce3597851110001cf62487ff98b9b260c476cad34369e08b30a08"
    
    perfil_coche = "driving-car"
    perfil_bici = "cycling-regular"
    perfil_pie = "foot-walking"

    # Coordenadas del destino (latitud, longitud)
    geo = Nominatim(user_agent = "Travel")
    destino_ciudad = input("Dime ciudad de destino: ")
    destino = obtener_coordenadas(destino_ciudad)
    if destino:
        origenes = []
        for i in range(5):
            nombre_ciudad = input(f"Ingrese el nombre de la ciudad {i+1}: ")
            coordenadas_ciudad = obtener_coordenadas(nombre_ciudad)
            if coordenadas_ciudad:
                origenes.append((nombre_ciudad, coordenadas_ciudad))

        rutas_calculadas = calcular_ruta([coordenadas for _, coordenadas in origenes], destino, [nombre for nombre, _ in origenes])
        
        mejores_rutas_ordenadas = sorted(rutas_calculadas, key=lambda x: x['Distancia'])
        # Agrupar elementos con las mismas coordenadas de aeropuerto cercano
        sublistas_agrupadas = [list(group) for _, group in groupby(mejores_rutas_ordenadas, key=lambda x: x['Aeropuerto'])]

    def filtrar_sublista_y_listar_eliminados(sublista):
        elementos_eliminados = list(filter(lambda x: x['Tiempo'] < 0.75, sublista))
        sublista_filtrada = list(filter(lambda x: x['Tiempo'] >= 0.75, sublista))    
        return sublista_filtrada

    # Aplicar la función de filtrado y listado a cada sublista y reasignar las sublistas filtradas
    sublistas_filtradas = [filtrar_sublista_y_listar_eliminados(sublista) for sublista in sublistas_agrupadas]

    # Función para calcular la distancia entre dos puntos
    def calcular_distancia(coord1, coord2):
        return geodesic(coord1, coord2).kilometers
    
    for sublista in sublistas_filtradas:
        for i in range(len(sublista)):
            for j in range(i + 1, len(sublista)):
                distancia_entre_puntos = calcular_distancia((sublista[i]['Destino'][1], sublista[i]['Destino'][0]), (sublista[j]['Destino'][1], sublista[j]['Destino'][0]))
                if distancia_entre_puntos > 20:
                    print(f"La Persona {sublista[i]['Persona']} se dirige en coche hacia {sublista[i]['Aeropuerto']['Nombre']}")
                    sublista.pop(i)
                    break
    # Llamar a la función
    eliminar_y_mostrar_info(sublistas_filtradas)
    mejor_vuelo_para_destino(sublistas_filtradas, destino)     
