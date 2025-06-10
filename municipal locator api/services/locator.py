from utlis import load_municipal_data, point_in_polygon

def locate_by_coordinates(lat,lon):
    data = load_municipal_data()
    for province in data['provinces']:
        for district in province['districts']:
            if 'geometry' in district:
                found = point_in_polygon(lat, lon, [district])
                if found:
                    return {
                        "province": province['name'],
                        "district": district['name'],
                        "type": district["type"],
                        "code": district["code"]
                    }
                for lm in district.get("local_municipalities", []):
                    if "geometry" in lm:
                        found = point_in_polygon(lat, lon, [lm])
                        if found:
                             return {
                        "province": province['name'],
                        "district": district['name'],
                        "type": lm["type"],
                        "code": lm["code"]
                    }
    return None                
      
                


