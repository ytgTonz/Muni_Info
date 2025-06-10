import json
from shapely.geometry import shape, Point
from config import DATA_PATH

def load_municipal_data():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load()

def point_in_polygon(lat,lon,polygons):
    point = Point(lon,lat)
    for item in polygons:
        geom = shape(item['geometry'])
        if geom.contains(point):
            return item
    return None    
    