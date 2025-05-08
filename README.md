# Bike Station Distance Calculator

This script calculates the pairwise shortest bike network distances between bike stations using the GraphHopper API. It processes the data in batches to handle large numbers of stations efficiently.

Install the required packages using:
```bash
pip install numpy pandas requests
```

## Input Data

The script expects a CSV file named `stations.csv` with the following columns:
- ID: Station identifier of bike station
- lat: Latitude of the bike station
- lon: Longitude of the bike station

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

### How it Works

1. The full 1836x1836 matrix is divided into 80x80 windows
2. Each window represents distance calculations between 80 origin and 80 destination stations
3. Windows are processed sequentially, respecting the 20.1s rate limit
4. Results are combined into the final distance matrix

## GraphHopper API Configuration

- Subscription Plan: Pro
- Rate Limit: 1 request per 20.1 seconds
- Matrix Size Limit: 80x80 per request
- Vehicle Type: bike


## Output

The script generates a CSV file named `bike_station_distances.csv` containing the pairwise distances between all stations. The distances are in meters.


## Notes

- For large datasets, the calculation may take a significant amount of time due to the rate limiting
- The output matrix isnt symmetric

## Requirements

- Python 3.6+
- Required packages:
  - numpy
  - pandas
  - requests
  
## Error Handling

The script includes comprehensive error handling for:
- File reading errors
- API request failures
- Missing API key
- Data processing errors

All errors are logged with appropriate messages to help with debugging. 

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.


