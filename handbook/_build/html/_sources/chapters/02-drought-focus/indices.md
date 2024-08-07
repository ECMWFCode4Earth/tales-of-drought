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

This global **SPI** is calculated using data from the era5-dataset. This **SPI** can examine rainfall over various timescales, including 1, 3, 6, 12, 24, 36 and 48 months, allowing for a detailed analysis of short-term fluctuations and long-term trends in precipitation.


```{tip} 
If you're interested in learning more about the **SPI** index, you can download the  "[Standardized Precipitation Index User Guide](https://library.wmo.int/records/item/39629-standardized-precipitation-index-user-guide)" from the World Meteorological Organization (WMO).
```


## SPEI index


The **Standardized Precipitation Evapotranspiration Index** (**SPEI**) is a widely used meteorological index for measuring drought conditions. The **SPEI** quantifies the deficit of water on the land's surface over various time periods, typically spanning months. It is designed to take into account both precipitation and potential PET in determining drought.

In simpler terms, the **SPEI** scores indicate how wet or dry a period is compared to normal conditions, using standard-deviation from the mean: negative values indicate drier than usual periods while positive values correspond to wetter than usual periods. The magnitude of the SPEI is an indicator of the severity of event.  
**SPEI** values ranging from -1 to 1 are generally viewed as normal. 


Here's what the scores typically represent:

- SPEI > 2.0: extremely wet  
- 1.5 < SPEI <= 2.0: severely wet  
- 1.0 < SPEI <= 1.5: moderately wet  
- 0 < SPEI <= 1.0: near-normal / mildly wet  
- –1.0 < SPEI <= 0: near-normal / mildly dry  
- –1.5 < SPEI <= –1.0: moderately dry  
- –2.0 < SPEI <= –1.5: severely dry  
- SPEI < –2.0: extremely dry


The **SPEI** is typically computed over a range of time windows from 1 over 3 and 6 to 12 months or more. The time window considered is indicative of the potential impact of meteorological drought, which is often the primary driver of drought.


```{tip} 
- The SPEI developed by Vicente-Serrano and colleagues in 2010, here you can find the orignal paper [A Multiscalar Drought Index Sensitive to Global Warming: The Standardized Precipitation Evapotranspiration Index](https://journals.ametsoc.org/view/journals/clim/23/7/2009jcli2909.1.xml) 
- If you'd like to go deeper about drought indicators and indices, you can read the "[Handbook of Drought Indicators and Indices](https://library.wmo.int/doc_num.php?explnum_id=3057)" by the World Meteorological Organization (WMO).
```

