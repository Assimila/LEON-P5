// ============================================
// Download Natural Forest 2020 from GEE
// ============================================

// Define your regions
var regions = {
  denmark: ee.Geometry.Rectangle([8.0763890, 54.5590290, 15.1930560, 57.7515260]),
  netherlands: ee.Geometry.Rectangle([3.3607822, 50.7234917, 7.2270951, 53.5545850]),
};

// Load the dataset
var probabilities = ee.ImageCollection(
  'projects/nature-trace/assets/forest_typology/natural_forest_2020_v1_0_collection')
  .mosaic()
  .select('B0');

// Visualize
Map.addLayer(
  probabilities.mask(probabilities.neq(0)),
  {min: 0, max: 250, palette: ['white', 'green']},
  'Natural forest probabilities'
);

//__EXPORT__//

// Denmark
Export.image.toDrive({
  image: probabilities.clip(regions.denmark),
  description: 'natural_forest_denmark_2020',
  folder: 'GEE_Exports',
  fileNamePrefix: 'natural_forest_denmark',
  scale: 10,
  region: regions.denmark,
  maxPixels: 1e13,
  crs: 'EPSG:3035'
});

// Netherlands
Export.image.toDrive({
  image: probabilities.clip(regions.netherlands),
  description: 'natural_forest_netherlands_2020',
  folder: 'GEE_Exports',
  fileNamePrefix: 'natural_forest_netherlands',
  scale: 10,
  region: regions.netherlands,
  maxPixels: 1e13,
  crs: 'EPSG:3035'
});

print('✓ Export tasks created!');
print('Check Tasks tab to run each task');