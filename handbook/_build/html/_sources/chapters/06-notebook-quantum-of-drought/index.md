# Quantum of drought: evaluating drought anomalies

## Purpose of the notebook
Explain the objective of the notebook, which is to guide users through the process of quantifying the severity and anomalies of drought events.


## Recap of Notebook 1
In the first notebook, we focused on identifying drought events globally using the SPI and SPEI indices. We explored how these indices are calculated and their significance in determining drought conditions across different regions and times.


## Indicators of interest
We will concentrate on the SPI and SPEI values from our dataset, covering the period from 1940 to the present. The data quality will be assessed, noting any limitations such as missing data or measurement errors that could influence our analysis.


## Understanding drought severity and anomalies

We will begin by defining drought severity and anomalies, explaining how indices like SPI and SPEI contribute to our understanding of these phenomena. The section will clarify the metrics used to measure drought intensity and irregularities in climatic patterns.


## Data loading and preprocessing
- Getting the data: we will describe the source of our dataset, primarily focusing on the distribution of SPI and SPEI values in NetCDF format.
- Loading data: instructions on how to load these indices using Python libraries like xarray for handling multidimensional arrays.
- Data inspection: a walkthrough of the dataset’s structure, highlighting important variables, their dimensions, and accessing metadata.
- Preprocessing steps: necessary steps such as handling missing values, aligning time series data, and normalizing the indices will be covered.


## Analytical Methods to evaluate drought anomalies

### Statistical methods:
- Standard deviations: we will calculate how significantly current drought events deviate from the historical average.
- Percentiles and ranking: this will involve ranking current droughts against historical events to ascertain their relative severity.

### Visual methods:
- Time series plots: creating plots to show long-term trends in SPI and SPEI values.
- Histograms: these will help understand the frequency distribution of drought severities.
- Box plots: to visualize the range, median, and outliers in the drought data.


## Case study

We will select a specific year noted for severe drought and analyze it using the tools discussed. This will include calculating standard deviation and percentiles, and visualizing the data through various graphical representations.


## Interactive component

We'll implement an interactive feature allowing users to select a year or range of years. They will be able to generate a custom analysis of drought severity and anomalies for their chosen period.


## Conclusion

- Summarize key findings on the severity and anomalies of droughts.
- How can this information help?


## Preview of what’s coming in Notebook 3 