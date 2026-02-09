// Download in GEE MODIS NPP data for Denmark and the Netherlands for specified years, clip to bounding boxes, and export to Google Drive.

// Bounding boxes
var BBOXES = {
  'dnk': ee.Geometry.Rectangle([8.076389, 54.559029, 15.193056, 57.751526]),
  'nld': ee.Geometry.Rectangle([3.360782, 50.723492, 7.227095, 53.554585])
};

// Years to process (add more years to this array as needed)
var years = [2018];

// Visualization parameters
var visualization = {
  bands: ['Npp'],
  min: 0,
  max: 19000,
  palette: ['bbe029', '0a9501', '074b03']
};

// Dataset
var dataset = ee.ImageCollection('MODIS/061/MOD17A3HGF');

// Loop through years
years.forEach(function(year) {
  
  // Filter dataset for the specific year
  var startDate = ee.Date.fromYMD(year, 1, 1);
  var endDate = ee.Date.fromYMD(year, 12, 31);
  
  var yearlyData = dataset
    .filterDate(startDate, endDate)
    .first(); // MOD17A3HGF is annual, so one image per year
  
  // Loop through each bounding box
  Object.keys(BBOXES).forEach(function(region) {
    var bbox = BBOXES[region];
    
    // Clip to region
    var clipped = yearlyData.clip(bbox);
    
    // Add to map for visualization
    Map.addLayer(clipped, visualization, region + '_NPP_' + year);
    
    // Export to Google Drive
    Export.image.toDrive({
      image: clipped.select('Npp'),
      description: 'NPP_' + region + '_' + year,
      folder: 'GEE_Exports', // Change folder name as needed
      region: bbox,
      scale: 500, // MODIS resolution is 500m
      crs: 'EPSG:4326',
      maxPixels: 1e13
    });
  });
});

// Center map on Europe
Map.setCenter(10.0, 54.0, 5);

print('Export tasks configured. Click "Run" in the Tasks tab to start exports.');