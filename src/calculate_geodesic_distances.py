import pandas as pd
import numpy as np
from geopy.distance import geodesic
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def read_stations():
    """Read station data from CSV file."""
    try:
        return pd.read_csv('data/stations.csv')
    except FileNotFoundError:
        logging.error("stations.csv not found in data directory")
        raise

def calculate_geodesic_distances(stations):
    """Calculate pairwise geodesic distances between stations."""
    n_stations = len(stations)
    distances = np.zeros((n_stations, n_stations))
    
    for i in range(n_stations):
        for j in range(n_stations):
            if i != j:
                point1 = (stations.iloc[i]['lat'], stations.iloc[i]['lon'])
                point2 = (stations.iloc[j]['lat'], stations.iloc[j]['lon'])
                distances[i, j] = geodesic(point1, point2).meters
            else:
                distances[i, j] = 0
                
        logging.info(f"Processed station {i+1}/{n_stations}")
    
    return distances

def save_distances(distances, stations):
    """Save distance matrix to CSV file."""
    # Create DataFrame with station IDs as index and columns
    df = pd.DataFrame(
        distances,
        index=stations['ID'],
        columns=stations['ID']
    )
    
    # Save to CSV
    output_file = 'data/geopy_distance.csv'
    df.to_csv(output_file)
    logging.info(f"Successfully saved geodesic distances to {output_file}")

def main():
    try:
        # Read station data
        stations = read_stations()
        logging.info(f"Read {len(stations)} stations from data/stations.csv")
        
        # Calculate distances
        distances = calculate_geodesic_distances(stations)
        
        # Save results
        save_distances(distances, stations)
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main() 