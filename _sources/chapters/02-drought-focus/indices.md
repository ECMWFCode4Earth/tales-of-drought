# Drought indicators and indices

Indicators and indices are the tools that let us to understand the drought phenomenon.

**Indicators** are variables or parameters used to describe drought conditions. They include precipitation, temperature, streamflow, groundwater and reservoir levels, soil moisture and snowpack.

Drought **indices** are tools to measure how severe a drought is. They help us understand the current state of droughts by evaluating various climate conditions. These indices are helpful because they break down complex weather data into simpler terms, making it easier for everyone to understand. 

They also indicate the severity, location, timing, and duration of droughts. For instance, severity is how much the current situation differs from normal weather patterns. The indices can also show us the specific area affected by the drought, when the drought started, and how long it might last. 

This information is crucial for planning how to respond to droughts, especially in how they affect people, farms, and water supplies. The impact of a drought can vary; for example, a short drought during a critical time for crops can be more harmful than a longer, more severe drought at another time.

There are various methods to monitor a drought: 
- we can use a single indicator or index
- we can use multiple indicators or indices
- we can use composite or hybrid indicators

For our analysis we will focus on two indices: **SPI** and **SPEI**.


## SPI index

The **Standardized Precipitation Index** (**SPI**) is an index used to measure drought intensity. It works by comparing the amount of rainfall in a specific period to the historical average for that same period. This helps determine how much more, or less, it has rained compared to usual conditions. 

This global **SPI** is calculated using data from the era5-dataset. This **SPI** can examine rainfall over various timescales (accumulation windows), including 1, 3, 6, 12, 24, 36 and 48 months, allowing for a detailed analysis of short-term fluctuations and long-term trends in precipitation. The appropriate choice of time scale depends on the specific drought impact: values for 1 and 3 months are useful for the basic drought monitoring, 6 months or less are suitable for assessing agricultural impacts, and 12 months or longer are relevant for monitoring hydrological impacts.



```{tip} 
If you're interested in learning more about the **SPI** index, you can download the  "[Standardized Precipitation Index User Guide](https://library.wmo.int/records/item/39629-standardized-precipitation-index-user-guide)" from the World Meteorological Organization (WMO).
```


## SPEI index


The **Standardized Precipitation Evapotranspiration Index** (**SPEI**) is a widely used meteorological index for measuring drought conditions. The **SPEI** quantifies the deficit of water on the land's surface over various time periods, typically spanning months. It is designed to take into account both precipitation and potential evapotranspiration (PET) in determining drought.

In simpler terms, the **SPEI** scores indicate how wet or dry a period is compared to normal conditions, using standard-deviation from the mean: negative values indicate drier than usual periods while positive values correspond to wetter than usual periods. The magnitude of the SPEI is an indicator of the severity of event.  


The **SPEI** is typically computed over a range of time windows from 1 over 3 and 6 to 12 months or more (24, 36, 48 months). Similar to the SPI index, the chosen time window helps identify and monitor conditions associated with various drought impacts.

**SPI** and **SPEI** values are in units of standard deviation from the standardised mean. The magnitude of these indices indicates the severity of drought events: values between -1 and 1 are generally considered normal, while values outside this range indicate either drier-than-usual or wetter-than-usual conditions.

**SPI** and **SPEI** values ranging from -1 to 1 are generally viewed as normal. 

Here's what the scores typically represent:

- SPI/SPEI > 2.0: extremely wet  
- 1.5 < SPI/SPEI <= 2.0: severely wet  
- 1.0 < SPI/SPEI <= 1.5: moderately wet  
- 0 < SPI/SPEI <= 1.0: near-normal / mildly wet  
- –1.0 < SPI/SPEI <= 0: near-normal / mildly dry  
- –1.5 < SPI/SPEI <= –1.0: moderately dry  
- –2.0 < SPI/SPEI <= –1.5: severely dry  
- SPI/SPEI < –2.0: extremely dry

There are significant differences in the sensitivity of SPI and SPEI values at different time scales: the smaller the time scale, the more the wet and dry changes.

Being standardized indices makes them unitless measures, which facilitates comparative analysis across diverse time series
datasets.


```{tip} 
- The SPEI developed by Vicente-Serrano and colleagues in 2010, here you can find the orignal paper [A Multiscalar Drought Index Sensitive to Global Warming: The Standardized Precipitation Evapotranspiration Index](https://journals.ametsoc.org/view/journals/clim/23/7/2009jcli2909.1.xml) 
- If you'd like to go deeper about drought indicators and indices, you can read the "[Handbook of Drought Indicators and Indices](https://library.wmo.int/doc_num.php?explnum_id=3057)" by the World Meteorological Organization (WMO).
```

