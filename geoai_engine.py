import ee

def initialize_ee():
    try:
        ee.Initialize()
        return True
    except Exception as e:
        print("Помилка ініціалізації Earth Engine. Переконайтесь, що виконали `earthengine authenticate`.")
        return False

def get_ndvi_time_series(roi_polygon, start_date='2023-01-01', end_date='2025-12-31'):
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
           .filterBounds(roi_polygon) \
           .filterDate(start_date, end_date) \
           .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
           
    def add_ndvi(image):
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        return image.addBands(ndvi)
        
    return s2.map(add_ndvi)

def check_viirs_nightlights(roi_polygon, year='2025'):
    dataset = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG") \
                .filterBounds(roi_polygon) \
                .filterDate(f'{year}-01-01', f'{year}-12-31')
    
    return dataset.select('avg_rad').mean()