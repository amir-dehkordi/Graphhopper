# Bike Station Distance Calculator

This script calculates the pairwise shortest bike distances between bike stations using the GraphHopper API. It processes the data in batches to handle large numbers of stations efficiently.

## Requirements

- Python 3.6+
- Required packages:
  - numpy
  - pandas
  - requests

Install the required packages using:
```bash
pip install numpy pandas requests
```

## Input Data

The script expects a CSV file named `202306.csv` with the following columns:
- ID: Station identifier
- lat: Latitude of the station
- lon: Longitude of the station

## Usage

1. Set your GraphHopper API key as an environment variable:
```bash
# On Windows
set GRAPHHOPPER_API_KEY=your_api_key_here

# On Linux/Mac
export GRAPHHOPPER_API_KEY=your_api_key_here
```

2. Run the script:
```bash
python bike_station_distances.py
```

## Output

The script generates a CSV file named `bike_station_distances.csv` containing the pairwise distances between all stations. The distances are in meters.

## Features

- Processes stations in batches to handle large datasets
- Implements rate limiting for API calls (60.1 seconds between calls for free plan)
- Comprehensive error handling and logging
- Progress tracking during calculation

## Notes

- The script uses the free tier of GraphHopper API which has rate limits
- For large datasets, the calculation may take a significant amount of time due to the rate limiting
- The output matrix is symmetric (distance from A to B equals distance from B to A)

## Error Handling

The script includes comprehensive error handling for:
- File reading errors
- API request failures
- Missing API key
- Data processing errors

All errors are logged with appropriate messages to help with debugging. 