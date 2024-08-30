# Climate data sources

Working with climate data, we will encounter the following definitions: observations, reanalyses, and climate models. What do they mean, and what are the differences?  
These represent three major categories of data sources, and the choice of which one to use depends on the time period we are interested in.

![](../../images/data-sources.svg)


## Observations

The **observations** measure the variables at specific times and places. They can be obtained with in-situ technologies, such as ground stations, or with remote technologies, such as satellite and radars.  
The observations are defined **direct** when the variables are measured directly, and **indirect** when they are inferred from other observations.

![](../../images/obs_inputs.png)
<p class="credits">Observation components of the Global Observing System - <a href="https://www.ecmwf.int/en/research/data-assimilation/observations" target="_blank">ECMWF</a></p>


## Climate models

The second category of data sources comprises climate models, which are mathematical representations used to comprehend and forecast climate systems. These models vary, each designed to examine distinct facets of the climate.  
With the advancement of computing capabilities over recent decades, these models have also grown more complex. 
These models don't predict specific events at particular times or locations, but are used for assessing how average and extreme climate conditions are expected to shift.

![](../../images/dev-climate-models.svg)
<p class="credits">Elaboration from the original - <a href="https://climate.nasa.gov/news/830/climate-modelers-and-the-moth/" target="_blank">NASA's Goddard Space Flight Center</a></p>


### The model grid

Even if the computing power has increased, it is however impossible to compute the climate state of every possible points on the planet. What the models do is to compute the climate state of regularly spaced points, creating *de facto* a grid with each point at the center of its cell. The value is considered to be an average of the grid cell.

When dealing with climate data, we have to consider that climate is related not only to the Earth surface (that we have already seen how it can be represented through [a system of coordinates](https://ecmwfcode4earth.github.io/tales-of-drought/chapters/01-climate-toolkit-for-beginners/coordinate-system.html)), but also to atmospheric conditions. So we have to add a third dimension to our system, named ‘height’ or ‘pressure’ and also divided into cells.

However, climate evolves over time, so we must consider it as a fourth dimension.

![](../../images/grid.svg)


The effectiveness of a climate model is influenced by its resolution, which includes both spatial and temporal aspects. **Spatial resolution** determines the dimensions of the grid cells within the model, measurable in degrees of latitude and longitude or kilometers. **Temporal resolution**, on the other hand, defines the frequency of computations for various quantities within the model. Frequently, a single model can operate at varying resolutions, and the selection of resolution depends on the particular issue being investigated.


## Reanalyses

Climate reanalyses combine historical observations with models to create time series for various climate variables. Reanalyses are highly utilized in the geophysical sciences since they offer a detailed account of the climate as observed over recent decades.  
The quality of a reanalysis depends on the resolution of its model as well as the quality of observations.  
ERA5 is the latest climate reanalysis produced by ECMWF. It is available from 1940 and continues to be extended forward in time. 

![](../../images/reanalysis-stages.png)
<p class="credits">Three stages of reanalysis - <a href="https://climate.copernicus.eu/copernicus-regional-reanalysis-europe-cerra" target="_blank">Copernicus Climate Change Service</a></p>


 ## The drought dataset
The dataset we'll be using is [**ERA5-DROUGHT**](https://cds.climate.copernicus.eu/cdsapp#!/dataset/dderived-drought-historical?tab=overview), which is derived from the ERA5 reanalysis provided by the European Centre for Medium-Range Weather Forecasts (ECMWF). This dataset includes two primary standardized drought indicators:

- The Standardized Precipitation Index (SPI)
- The Standardized Precipitation-Evapotranspiration Index (SPEI)

The [next chapter](https://ecmwfcode4earth.github.io/tales-of-drought/chapters/02-drought-focus/indices.html) takes an in-depth look at these two indices.


```{tip} 
If you are interested to learn more about climate data sources, you can watch the three ECMWF's course:
- [Data Resources - Observations](https://learning.ecmwf.int/course/view.php?id=64)
- [Data Resources - Reanalyses](https://learning.ecmwf.int/course/view.php?id=63)
- [Data Resources - Climate Models](https://learning.ecmwf.int/course/view.php?id=62)

Read this slides:
- [Data Resources - Climate Models](https://climate.copernicus.eu/sites/default/files/2021-12/10-c3s-uls-data-resources-climate-models.pdf)

Or you can visit the webpages:
- [Observation components of the Global Observing System](https://community.wmo.int/en/observation-components-global-observing-system) of the World Meteorological Organization (WMO).
- [Basics of Global Climate Models](https://www.climatehubs.usda.gov/hubs/northwest/topic/basics-global-climate-models) of the USDA Climate Hubs
- [Climate reanalysis](https://climate.copernicus.eu/climate-reanalysis) of Copernicus
```