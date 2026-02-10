#### The following uses De Palma (2024) as point of departure ####
# https://adrianadepalma.github.io/BII_tutorial/#Calculate_diversity_indices

# reading  packages 
pack<-c("tidyr","dplyr","tibble","lme4","car","betapart","terra","geosphere","purrr","furrr","viridis", "ggplot2","maps","predictsr")
lapply(pack, require, character.only=T)

## setting working path
data_path<-"C:/Users/rxk441/OneDrive - University of Copenhagen/Documents/LEON"
setwd(data_path)
getwd()

dir()

predicts <- GetPredictsData()
summaries <- GetSitelevelSummaries()
columns <- GetColumnDescriptions()

table(predicts$Country) # There are 129 measurements from Denmark.
table(predicts$UN_region) # There are 1,373,389 measurements from Europe.

table(predicts$Predominant_land_use, predicts$Use_intensity)

#### Making one variable with all the land uses and intensities ####
predicts$LandUse<-NA
predicts <- predicts |>
  dplyr::mutate(LandUse = paste(Predominant_land_use, Use_intensity, sep = " "))
table(predicts$LandUse)
world<-predicts

# Ensuring that you can change "cannot decide" land uses into NA, but also that you can choose not to, by not running the next 10 lines. 
world$LandUse2<-NA  
world <- world |>
  dplyr::mutate(
    LandUse2 = ifelse(Predominant_land_use == "Cannot decide",
                      NA,
                      paste(LandUse)),)

world <- world[ -c(68) ]
world <- world %>% 
  rename("LandUse"="LandUse2")

table(world$LandUse)

world <- world |>
  dplyr::mutate(
    # relevel the factor so that Primary minimal is the first level (so that it is the intercept term in models)
    LandUse = factor(LandUse),
    LandUse = relevel(LandUse, ref = "Primary vegetation Minimal use"))


#### Calculate diversity indices - Total abundance #### 
# We are using the Effort_corrected_measurement instead of measurement directly to account for the fact that sampling effort can vary among sites.
# To see how much it influences results, you can run this:

# world$difference <- NA
# world$difference <- world$Measurement - world$Effort_corrected_measurement or this code does the same: world <- world |>
# dplyr::mutate(difference = Measurement - Effort_corrected_measurement)

# and get this:
# summary(world$difference)
# Min.   1st Qu.    Median      Mean   3rd Qu.      Max. 
# -9581.000     0.000     0.000    -0.195     0.000     0.000 
# So, while for a very small subset (of primarily worm species), sampling effort means a lot, for the vast majority of observations, it does not.

abundance_data <- world |>
  
  # pull out just the abundance measures
  dplyr::filter(Diversity_metric_type == "Abundance") |>
  
  # group by SSBS (each unique value corresponds to a unique site)
  dplyr::group_by(SSBS) |>
  
  # now add up all the abundance measurements within each site
  dplyr::mutate(TotalAbundance = sum(Effort_corrected_measurement)) |>
  
  # ungroup
  dplyr::ungroup() |>
  
  # pull out unique sites
  dplyr::distinct(SSBS, .keep_all = TRUE) |>
  
  # now group by Study ID
  dplyr::group_by(SS) |>
  
  # pull out the maximum abundance for each study
  dplyr::mutate(MaxAbundance = max(TotalAbundance)) |>
  
  # ungroup
  dplyr::ungroup() |>
  
  # now rescale total abundance, so that within each study, abundance varies from 0 to 1.
  dplyr::mutate(RescaledAbundance = TotalAbundance/MaxAbundance)
# saveRDS(abundance_data, "abundance_world.rds")
# abundance_data<-readRDS("abundance_world.rds")

#### Calculate diversity indices - Compositional Similarity #### 
# Using the balanced Bray-Curtis Index as our measure of compositional similarity. 
# It considers changes in community structure, rather than just identity as the less sensitive asymmetric Jaccard Index, does.
# Several indices of compositional similarity exist.
cd_data_input <- world |>
  # drop any rows with unknown LandUse
  dplyr::filter(!is.na(LandUse)) |>
  # pull out only the abundance data
  dplyr::filter(Diversity_metric_type == "Abundance") |>
  # group by Study
  dplyr::group_by(SS) |>
  # calculate the number of unique sampling efforts within that study
  dplyr::mutate(n_sample_effort = dplyr::n_distinct(Sampling_effort)) |>
  # calculate the number of unique species sampled in that study
  dplyr::mutate(n_species = dplyr::n_distinct(Taxon_name_entered)) |>
  # check if there are any Primary minimal sites in the dataset 
  dplyr::mutate(n_primin_records = sum(LandUse == "Primary vegetation Minimal use")) |>
  # ungroup
  dplyr::ungroup() |>
  # now keep only the studies with one unique sampling effort
  dplyr::filter(n_sample_effort == 1) |>
  # and keep only studies with more than one species 
  dplyr::filter(n_species > 1) |>
  # and keep only studies with at least some Primary minimal data
  dplyr::filter(n_primin_records > 0) |>
  # drop empty factor levels
  droplevels()

# GET THE VECTOR OF STUDIES 
studies <- cd_data_input |>
  dplyr::distinct(SS) |>
  dplyr::pull()

# CREATE SITE_COMPARISONS 
site_comparisons <- purrr::map_dfr(
  .x = studies, 
  .f = function(x){
    
    site_data <- dplyr::filter(cd_data_input, SS == x) |>
      dplyr::select(SSBS, LandUse) |>
      dplyr::distinct(SSBS, .keep_all = TRUE)
    
    baseline_sites <- site_data |>
      dplyr::filter(LandUse == "Primary vegetation Minimal use") |>
      dplyr::pull(SSBS)
    
    site_list <- site_data |>
      dplyr::pull(SSBS)
    
    site_comparisons <- expand.grid(baseline_sites, site_list) |>
      dplyr::rename(s1 = Var1, s2 = Var2) |>
      dplyr::filter(s1 != s2) |>
      dplyr::mutate(
        s1 = as.character(s1),
        s2 = as.character(s2),
        contrast = paste(s1, "vs", s2, sep = "_"),
        SS = as.character(x)
      )
    
    return(site_comparisons)
  }
)

# Now pre-process data once before the loop
cd_data_wide <- cd_data_input |>
  dplyr::select(SSBS, Taxon_name_entered, Measurement) |>
  tidyr::pivot_wider(names_from = Taxon_name_entered, values_from = Measurement, values_fill = 0) |>
  tibble::column_to_rownames("SSBS")

# Modified function that uses pre-processed data
get_bray_optimized <- function(s1, s2, data_wide){
  
  sp_data <- data_wide[c(s1, s2), , drop = FALSE]
  
  if(sum(rowSums(sp_data, na.rm = TRUE) == 0) == 1){
    bray <- 0
  } else if(sum(rowSums(sp_data, na.rm = TRUE) == 0) == 2){
    bray <- NA
  } else {
    bray <- 1 - 
      betapart::bray.part(sp_data) |>
      purrr::pluck("bray.bal") |>
      purrr::pluck(1)
  }
  
  return(bray)
}

# 
options(future.globals.maxSize = 2000 * 1024^2)
# Set up parallel processing
future::plan("multisession", workers = 2) # The following code can also be run with all workers minus one, but it can be prone to crashing!

# Calculate Bray-Curtis (this takes a while)
bray <- furrr::future_map2_dbl(
  .x = site_comparisons$s1,
  .y = site_comparisons$s2,
  ~get_bray_optimized(s1 = .x, s2 = .y, data_wide = cd_data_wide),
  .options = furrr::furrr_options(seed = TRUE)
)

# Stop parallel processing
future::plan("sequential")


# for the other required information, we don't need to run loops
latlongs <- cd_data_input |>
  # for each site in the dataset
  dplyr::group_by(SSBS) |>
  # pull out the lat and long
  dplyr::summarise(
    Lat = unique(Latitude),
    Long = unique(Longitude)
  )

lus <- cd_data_input |>
  # for each site in the dataset
  dplyr::group_by(SSBS) |>
  # pull out the land use
  dplyr::summarise(lu = unique(LandUse))

# now let's put all the data together
cd_data <- site_comparisons |>
  # add in the bray-curtis data
  # which is already in the same order as site_comparisons
  dplyr::mutate(bray = bray) |>
  # get the lat and long for s1
  dplyr::left_join(latlongs, by = c("s1" = "SSBS")) |>
  dplyr::rename(s1_lat = Lat, s1_long = Long) |>
  # get the lat and long for s2
  dplyr::left_join(latlongs, by = c("s2" = "SSBS")) |>
  dplyr::rename(s2_lat = Lat, s2_long = Long) |>
  # calculate the geographic distances between s1 and s2 sites
  dplyr::mutate(
    geog_dist = geosphere::distHaversine(
      cbind(s1_long, s1_lat), cbind(s2_long, s2_lat)
    )
  ) |>
  # get the land use for s1
  dplyr::left_join(lus, by = c("s1" = "SSBS")) |>
  dplyr::rename(s1_lu = lu) |>
  # get the land use for s2
  dplyr::left_join(lus, by = c("s2" = "SSBS")) |>
  dplyr::rename(s2_lu = lu) |>
  # create an lu_contrast column (what we'll use for modelling)
  dplyr::mutate(lu_contrast = paste(s1_lu, s2_lu, sep = "_vs_"))

# Save bray and cd_data for later use: 
# saveRDS(cd_data, "cd_world.rds")
# save(bray, file = "bray_world.RData")
# bray <- load("bray_world.RData")
# cd_data <- readRDS("cd_world.rds")


#### Run the statistical analysis - Total Abundance ####
# As De Palma (2024) notes, the errors in models of ecological abundance are generally non-normal. Therefore data is transformed.
# Choice of transformation depends on residual plots. 
table(abundance_data$Predominant_land_use, abundance_data$Use_intensity) #N.B.!

# A simple model (to this e.g. human population density can be added)
ab_m <- lme4::lmer(
  sqrt(RescaledAbundance) ~ LandUse + (1|SS) + (1|SSB), 
  data = abundance_data # Only abundance_data is used
)
summary(ab_m)

ab_res <-resid(ab_m)
ab_fitted <- fitted(ab_m)
plot(ab_fitted,ab_res)
abline(0,0)  
qqnorm(ab_res)
qqline(ab_res) 
plot(density(ab_res)) 

# Using e.g., log1p(RescaledAbundance) instead of sqrt(RescaledAbundance), the residual plots do not look as good. 
# The log1p transformation actually has a better (lower) REML value, which suggests it fits the data better, but the sqrt transformation is likely to give more valid results.
# Just looking at t values from the summary, results are similar. 

# t-values numerically higher than 1.96 are statistically significant with this sample size.
# Almost everything is here, except:
# - Intermediate secondary vegetation Minimal use
# - Mature secondary vegetation Intense use (:only 27 observations)
# - Pasture Minimal use
# - Plantation Minimal use
# - Primary light use 
# - Secondary vegetation (indeterminate age) Minimal use
# - Urban Cannot decide (:only 25 observations, possibly large variation within the group)
# - Urban Minimal use

# Primary vegetation intense use is significantly positive! 

# Other than that, the analysis shows that total abundance is likely higher in primary minimal sites.


#### Run the statistical analysis - Compositional Similarity ####
# "We include a measure of the geographic distance beween sites. 
# This allows us to discount natural turnover in species with distance. 
# You can also include environmental distance" (this could be based on Gower’s dissimilarity of climatic variables). 
# "You might also want to include additional pressure variables in the compositional similarity model, such as human population density and road density. 
# We usually do this by including the pressure at site 2 (the non-baseline site) as well as the difference in pressure between site 1 and site 2."

# The compositional similarity measure we use is bounded between 0 and 1 – this means the errors will probably not be normally distributed, and that a transformation of the data is needed.

# there is some data manipulation we want to do before modelling
cd_data <- dplyr::mutate(
  cd_data,
  
  # logit transform the compositional similarity
  logitCS = car::logit(bray, adjust = 0.001, percents = FALSE),
  
  # square root transform the compositional similarity (I added this)
  sqrtCS = sqrt(bray),
    
  # log10 transform the geographic distance between sites
  log10geo = log10(geog_dist + 1),
  
  # make primary minimal-primary minimal the baseline again
  lu_contrast = factor(lu_contrast), 
  lu_contrast = relevel(lu_contrast, ref = "Primary vegetation Minimal use_vs_Primary vegetation Minimal use")
)



# Model compositional similarity as a function of the land-use contrast and the geographic distance between sites
cd_m <- lme4::lmer(
  sqrtCS ~ lu_contrast + log10geo + (1|SS) + (1|s2), 
  data = cd_data
)
summary(cd_m)
# Most variance at the SS-level, clustering at the SS level is quite strong - observations within the same SS group are more similar than observations from different groups.
# Note that you can’t trust the significance values of these compositional similarity values, as the same site goes into multiple comparisons in the model (each Primary minimal site is compared to all other sites in the study, inflating p-values)
# For now, a random intercept for site 2 (s2) is added to account for this. In the next version of the code and output, 
# permutation tests will be used to see which effects are significant following de Palma et al. (2019), and the random intercept for site 2 (s2) will not be used above.

table(cd_data_input$Predominant_land_use, cd_data_input$Use_intensity)
# So, as a contrast to the version only using data from Europe, this works for all the the classifications, even "cannot decide".

cd_res <-resid(cd_m)
cd_fitted <- fitted(cd_m)
plot(cd_fitted,cd_res)
abline(0,0)
qqnorm(cd_res)
qqline(cd_res)
plot(density(cd_res))



#### Model predictions ####
# Using the the models to predict the abundance and compositional similarity in each land use class, ignoring the impact of random effects for now. In the next version, it can be tested if allowing random slopes gives a better model.
# First, the abundance model

# set up a dataframe with all the levels you want to predict diversity for, so all the land use classes in your model must be in here
newdata_ab <- data.frame(LandUse = levels(abundance_data$LandUse)) |>
  
  # now calculate the predicted diversity for each of these land-use levels
  # setting re.form = NA means random effect variance is ignored
  # then square the predictions (because we modelled the square root of abundance, so we have to back-transform it to get the real predicted values)
  dplyr::mutate(ab_m_preds = predict(ab_m, dplyr::across(dplyr::everything()), re.form = NA) ^ 2)


# now the compositional similarity model

# once again, set up the dataframe with all the levels you want to predict diversity for
# because we had an extra fixed effect in this model (log10geo), we also have to set a baseline level for this
# We're interested in the compositional similarity when we discount natural turnover, so we want to set this to a static value. 
# We'll use 0 here, but we can also set it to the median geographic distance in the original data or any other meaningful level.
newdata_cd <- data.frame(
  lu_contrast = levels(cd_data$lu_contrast),
  log10geo = 0
) |>
  dplyr::mutate(
    cd_m_preds = predict(cd_m, dplyr::across(dplyr::everything()), re.form = NA) ^ 2)

# It’s these predicted values (ab_m_preds and cd_m_preds) that we’re going to use. 
# We will multiply the predicted abundance and compositional similarity in each land-use class 
# with the area of the cell in that land-use class. 

# However, because we have a mixed effects model, the absolute values are somewhat meaningless. 
# Instead, we care about the relative values – what is the abundance or compositional similarity 
# relative to what we’d find if the whole landscape was still minimally-used primary vegetation.
# So once we have the predictions, we divide by the reference value 
# (the predicted abundance or compositional similarity if the whole cell was minimally-used primary vegetation).





#### Predict BII from land-use rasters ####
lu_props_input <- rast("lu_proportions_dnk_2018_v1.tif")
names(lu_props_input) # See all layer names
plot(lu_props_input)
# props_input<-as.data.frame(lu_props_input)

# Calculate the sum of all land use proportions for each cell
total_lu <- sum(lu_props_input)

# Rescale each layer by dividing by the total (where total > 0)
# This will make proportions sum to 1 for each cell, taking account for the fact that some of the cells have sea area.
lu_props  <- lu_props_input / total_lu

# Handle division by zero (pure sea pixels) - set to NA 
lu_props[total_lu == 0] <- NA
plot(lu_props)

ab_raster <- (  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Cropland Intense use'] * lu_props[["crop_intense"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Cropland Light use'] * lu_props[["crop_light"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Cropland Minimal use'] * lu_props[["crop_minimal"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Intermediate secondary vegetation Intense use'] * lu_props[["sv_intermediate_intense"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Intermediate secondary vegetation Light use'] * lu_props[["sv_intermediate_light"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Intermediate secondary vegetation Minimal use'] * lu_props[["sv_intermediate_minimal"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Secondary vegetation (indeterminate age) Intense use'] * lu_props[["sv_indeterminate_intense"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Secondary vegetation (indeterminate age) Light use'] * lu_props[["sv_indeterminate_light"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Secondary vegetation (indeterminate age) Minimal use'] * lu_props[["sv_indeterminate_minimal"]] +
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Mature secondary vegetation Intense use'] * lu_props[["sv_mature_intense"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Mature secondary vegetation Light use'] * lu_props[["sv_mature_light"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Mature secondary vegetation Minimal use'] * lu_props[["sv_mature_minimal"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Pasture Intense use'] * lu_props[["pasture_intense"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Pasture Light use'] * lu_props[["pasture_light"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Pasture Minimal use'] * lu_props[["pasture_minimal"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Plantation forest Intense use'] * lu_props[["plantation_intense"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Plantation forest Light use'] * lu_props[["plantation_light"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Plantation forest Minimal use'] * lu_props[["plantation_minimal"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Urban Intense use'] * lu_props[["urban_intense"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Urban Light use'] * lu_props[["urban_light"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Urban Minimal use'] * lu_props[["urban_minimal"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Young secondary vegetation Intense use'] * lu_props[["sv_young_intense"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Young secondary vegetation Light use'] * lu_props[["sv_young_light"]] + 
                  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Young secondary vegetation Minimal use'] * lu_props[["sv_young_minimal"]]) /
  
  # divide by the reference value (which here is 0.4142471)
  newdata_ab$ab_m_preds[newdata_ab$LandUse == 'Primary vegetation Minimal use']

terra::plot(ab_raster, col = viridis::viridis(20)) #plot(ab_raster works as well)
ab_raster 
ab_rasterdataframe<-as.data.frame(ab_raster)
summary(ab_rasterdataframe)
# The average abundance across this map is 0.8128. The max value is above 1; 1.0167.
# terra::writeRaster(ab_raster, "ab_world_DK_18.tif", filetype = "GTiff", overwrite = TRUE)


cd_raster <- (    newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Intermediate secondary vegetation Minimal use'] * lu_props[["sv_intermediate_minimal"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Cropland Intense use'] * lu_props[["crop_intense"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Cropland Light use'] * lu_props[["crop_light"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Cropland Minimal use'] * lu_props[["crop_minimal"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Intermediate secondary vegetation Intense use'] * lu_props[["sv_intermediate_intense"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Mature secondary vegetation Intense use'] * lu_props[["sv_mature_intense"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Mature secondary vegetation Light use'] * lu_props[["sv_mature_light"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Mature secondary vegetation Minimal use'] * lu_props[["sv_mature_minimal"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Pasture Intense use'] * lu_props[["pasture_intense"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Pasture Light use'] * lu_props[["pasture_light"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Secondary vegetation (indeterminate age) Intense use'] * lu_props[["sv_indeterminate_intense"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Pasture Minimal use'] * lu_props[["pasture_minimal"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Secondary vegetation (indeterminate age) Light use'] * lu_props[["sv_indeterminate_light"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Secondary vegetation (indeterminate age) Minimal use'] * lu_props[["sv_indeterminate_minimal"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Urban Intense use'] * lu_props[["urban_intense"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Urban Light use'] * lu_props[["urban_light"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Urban Minimal use'] * lu_props[["urban_minimal"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Young secondary vegetation Light use'] * lu_props[["sv_young_light"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Plantation forest Intense use'] * lu_props[["plantation_intense"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Plantation forest Light use'] * lu_props[["plantation_light"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Plantation forest Minimal use'] * lu_props[["plantation_minimal"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Young secondary vegetation Minimal use'] * lu_props[["sv_young_minimal"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Young secondary vegetation Intense use'] * lu_props[["sv_young_intense"]] +
                  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Intermediate secondary vegetation Light use'] * lu_props[["sv_intermediate_light"]]) /
  
  # divide by the reference value (which here is 0.7043293)
  newdata_cd$cd_m_preds[newdata_cd$lu_contrast == 'Primary vegetation Minimal use_vs_Primary vegetation Minimal use']

terra::plot(cd_raster, col = viridis::viridis(20))
cd_raster 
cd_rasterdataframe<-as.data.frame(cd_raster)
summary(cd_rasterdataframe)
# The average compositional similarity across this map is 0.6834.
# terra::writeRaster(cd_raster, "cd_world_DK_18.tif", filetype = "GTiff", overwrite = TRUE)

#The final step is to multiply the abundance and compositional similarity rasters together. 
bii <- ab_raster * cd_raster
terra::plot(bii, col = viridis::viridis(20)) # plot(bii) works as well
bii
biidataframe<-as.data.frame(bii)
summary(biidataframe)
# The average BII across this map is 0.5570. 
# terra::writeRaster(bii, "bii_world_DK_18.tif", filetype = "GTiff", overwrite = TRUE)
