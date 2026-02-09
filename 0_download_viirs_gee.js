// Download in GEE VIIRS Nightlights data for Denmark and the Netherlands as annual median for specified years, clip to bounding boxes, and export to Google Drive.

// Bounding boxes
var BBOXES = {
  'dnk': ee.Geometry.Rectangle([8.076389, 54.559029, 15.193056, 57.751526]),
  'nld': ee.Geometry.Rectangle([3.360782, 50.723492, 7.227095, 53.554585])
};

var vis = {
  "opacity": 1,
  "bands": ["avg_rad"],
  "min": 1,
  "max": 30,
  "palette": ["584d9f", "9c79c1", "c98cbe", "f2d192", "e2ee82"]
};

var npp_viirs_ntl = ee.ImageCollection('NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG');
var countries = ['nld', 'dnk'];
var years = [2018, 2019, 2020, 2021, 2022, 2023];

// Export settings
var REDUCER = 'median';  // or 'mean'
var SCALE = 500;  // meters (VIIRS native resolution is ~500m)
var EXPORT_TO_DRIVE = true;  // Set to false for Cloud Storage
var CLOUD_BUCKET = 'your-bucket-name';  // Only needed if EXPORT_TO_DRIVE = false
var FOLDER_NAME = 'VIIRS_NTL_Yearly';  // Folder in Drive or Cloud Storage

countries.forEach(function(country) {
  var bbox = BBOXES[country];
  
  years.forEach(function(year) {
    var startDate = ee.Date.fromYMD(year, 1, 1);
    var endDate = ee.Date.fromYMD(year + 1, 1, 1);
    
    var yearlyCollection = npp_viirs_ntl
      .filterDate(startDate, endDate)
      .filterBounds(bbox);
    
    // Apply chosen reducer
    var yearlyComposite = (REDUCER === 'median') 
      ? yearlyCollection.select('avg_rad').median()
      : yearlyCollection.select('avg_rad').mean();
    
    var maskedComposite = yearlyComposite
      .clip(bbox)
      .updateMask(yearlyComposite.neq(0));
    
    // Add to map
    var layerName = country.toUpperCase() + ' ' + year + ' (' + REDUCER + ')';
    Map.addLayer(maskedComposite, vis, layerName, false);
    
    // Export
    var fileName = 'VIIRS_NTL_' + country.toUpperCase() + '_' + year + '_' + REDUCER;
    
    if (EXPORT_TO_DRIVE) {
      // Export to Google Drive
      Export.image.toDrive({
        image: yearlyComposite,
        description: fileName,
        folder: FOLDER_NAME,
        fileNamePrefix: fileName,
        region: bbox,
        scale: SCALE,
        crs: 'EPSG:4326',
        maxPixels: 1e13,
        fileFormat: 'GeoTIFF'
      });
    } else {
      // Export to Google Cloud Storage
      Export.image.toCloudStorage({
        image: yearlyComposite,
        description: fileName,
        bucket: CLOUD_BUCKET,
        fileNamePrefix: FOLDER_NAME + '/' + fileName,
        region: bbox,
        scale: SCALE,
        crs: 'EPSG:4326',
        maxPixels: 1e13,
        fileFormat: 'GeoTIFF'
      });
    }
  });
});

Map.centerObject(BBOXES['nld'], 7);
print('Yearly ' + REDUCER + ' composites created (2018-2023)');
print('Check the Tasks tab to run exports');