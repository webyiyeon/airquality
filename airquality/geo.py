import geocoder

class Geo:
    @staticmethod
    def address_to_lat_lon(address:str):
        address = address.replace("광역시", "")
        address = address.replace("번길", "")
        start = address.find("(")
        if start != -1:
            end = address.find(")")
            address = address[:start] + address[end + 1:]

        g = geocoder.osm(address)
        if len(g) != 0:
            g = dict(g.json)
            result = [float(g.get('raw').get('lat')), float(g.get('raw').get('lon'))]
        else:
            result = [0, 0]
        return result 