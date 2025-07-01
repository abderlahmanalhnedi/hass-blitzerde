from homeassistant.const import (
    ATTR_LATITUDE,
    ATTR_LONGITUDE
)

class BlitzerItem:
    def getBackendId(item):
        return item['backend'].split("-")[-1]

    def getPicturePath(item):
        vmax = item['vmax']
        if vmax == '?':
            vmax = 'v'
        elif vmax == '/':
            vmax = 'redlight'
        
        if 'fixed' in item['info']:
            return 'fixed_' + vmax
        elif 'partly_fixed' in item['info']:
            return 'ts_' + vmax
        else:
            return 'mobile_' + vmax
    
    def getAttributes(item, location=True):
        attrs = {}
        attrs['backend'] = BlitzerItem.getBackendId(item)
        attrs['vmax'] = item['vmax']
        attrs['entity_picture'] = "https://map.blitzer.de/v5/images/" + BlitzerItem.getPicturePath(item) + ".svg"
        attrs['counter'] = item['counter']
        attrs['city'] = item['address']['city']
        attrs['street'] = item['address']['street']
        attrs['zip_code'] = item['address']['zip_code']
        if location:
            attrs[ATTR_LATITUDE] = item['lat']
            attrs[ATTR_LONGITUDE] = item['lng']
        if 'desc' in item['info']:
            attrs['description'] = item['info']['desc']
        return attrs
