import time
import numpy as np
import pandas as pd
import requests
import os
from typing import List, Tuple
import logging
from datetime import datetime
import json
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# GraphHopper API configuration
API_KEY = os.getenv('GRAPHHOPPER_API_KEY')
if not API_KEY:
    raise ValueError("GRAPHHOPPER_API_KEY not found in environment variables")

BASE_URL = "https://graphhopper.com/api/1/matrix"
VEHICLE = "bike"
RATE_LIMIT = 20.1  # seconds between requests
WINDOW_SIZE = 80   # maximum matrix size per request

class BikeStationDistanceCalculator:
    def __init__(self, api_key: str, rate_limit: float = 60.1):
        """
        Initialize the distance calculator.
        
        Args:
            api_key (str): GraphHopper API key
            rate_limit (float): Time to wait between API calls in seconds
        """
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.url = "https://graphhopper.com/api/1/matrix"
        self.progress_file = "distance_calculation_progress.json"
        self.temp_output = "temp_distances.csv"
        
    def load_progress(self) -> Tuple[np.ndarray, List[Tuple[int, int]]]:
        """
        Load progress from previous runs.
        
        Returns:
            Tuple[np.ndarray, List[Tuple[int, int]]]: Current distance matrix and list of processed batches
        """
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                progress = json.load(f)
                processed_batches = [(batch[0], batch[1]) for batch in progress['processed_batches']]
                return np.array(progress['distances']), processed_batches
        return None, []
    
    def save_progress(self, distances: np.ndarray, processed_batches: List[Tuple[int, int]]):
        """
        Save current progress to file.
        
        Args:
            distances (np.ndarray): Current distance matrix
            processed_batches (List[Tuple[int, int]]): List of processed batches
        """
        progress = {
            'distances': distances.tolist(),
            'processed_batches': processed_batches,
            'last_updated': datetime.now().isoformat()
        }
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f)
        
        # Also save current distances to temporary CSV
        pd.DataFrame(distances).to_csv(self.temp_output, index=False)
        
    def extract_coordinates(self, data: np.ndarray, start_idx: int, end_idx: int) -> List[List[float]]:
        """
        Extract coordinates from data array for the given range.
        
        Args:
            data (np.ndarray): Array containing station data
            start_idx (int): Start index
            end_idx (int): End index
            
        Returns:
            List[List[float]]: List of [lon, lat] coordinates
        """
        return [[data[i, 2], data[i, 1]] for i in range(start_idx, end_idx)]
    
    def calculate_distances(self, data: np.ndarray, batch_size: int = 80) -> np.ndarray:
        """
        Calculate pairwise distances between all stations.
        
        Args:
            data (np.ndarray): Array containing station data
            batch_size (int): Number of stations to process in each batch
            
        Returns:
            np.ndarray: Matrix of distances between all stations
        """
        n_stations = data.shape[0]
        
        # Try to load previous progress
        final_result, processed_batches = self.load_progress()
        if final_result is None:
            final_result = np.zeros((n_stations, n_stations))
        
        # Create batches
        indices = []
        prev = 0
        for i in range(batch_size, n_stations, batch_size):
            indices.append([prev, i])
            prev = i
        indices.append([prev, n_stations])
        
        # Process each batch
        for origin_idx in indices:
            # Skip if this batch was already processed
            if any(origin_idx[0] == batch[0] and origin_idx[1] == batch[1] for batch in processed_batches):
                logger.info(f"Skipping already processed batch: {origin_idx}")
                continue
                
            origins = self.extract_coordinates(data, origin_idx[0], origin_idx[1])
            
            for destination_idx in indices:
                destinations = self.extract_coordinates(data, destination_idx[0], destination_idx[1])
                
                try:
                    response = self._make_api_request(origins, destinations)
                    results = np.array(response["distances"])
                    
                    final_result[origin_idx[0]:origin_idx[1], 
                               destination_idx[0]:destination_idx[1]] = results
                    
                    logger.info(f"Processed: From {origin_idx} To {destination_idx}")
                    
                    # Save progress after each successful batch
                    processed_batches.append((origin_idx[0], origin_idx[1]))
                    self.save_progress(final_result, processed_batches)
                    
                except Exception as e:
                    logger.error(f"Error processing batch {origin_idx} to {destination_idx}: {str(e)}")
                    # Save progress even if there's an error
                    self.save_progress(final_result, processed_batches)
                    continue
                
                time.sleep(self.rate_limit)
        
        return final_result
    
    def _make_api_request(self, origins: List[List[float]], destinations: List[List[float]]) -> dict:
        """
        Make API request to GraphHopper.
        
        Args:
            origins (List[List[float]]): List of origin coordinates
            destinations (List[List[float]]): List of destination coordinates
            
        Returns:
            dict: API response
        """
        query = {"key": self.api_key}
        
        payload = {
            "from_points": origins,
            "to_points": destinations,
            "out_arrays": ["distances"],
            "vehicle": "bike"
        }
        
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(
            self.url,
            json=payload,
            headers=headers,
            params=query
        )
        
        response.raise_for_status()
        return response.json()

def read_stations():
    """Read station data from CSV file."""
    try:
        return pd.read_csv('data/stations.csv')
    except FileNotFoundError:
        logging.error("stations.csv not found in data directory")
        raise

def calculate_distances(stations):
    """Calculate pairwise distances between stations using GraphHopper API."""
    n_stations = len(stations)
    distances = np.full((n_stations, n_stations), np.nan)
    
    # Process in windows to respect API limits
    for i in range(0, n_stations, WINDOW_SIZE):
        for j in range(0, n_stations, WINDOW_SIZE):
            # Get window indices
            i_end = min(i + WINDOW_SIZE, n_stations)
            j_end = min(j + WINDOW_SIZE, n_stations)
            
            # Prepare points for API request
            points = []
            for idx in range(i, i_end):
                points.append({
                    "lat": stations.iloc[idx]['lat'],
                    "lon": stations.iloc[idx]['lon']
                })
            for idx in range(j, j_end):
                points.append({
                    "lat": stations.iloc[idx]['lat'],
                    "lon": stations.iloc[idx]['lon']
                })
            
            # Make API request
            try:
                response = requests.post(
                    BASE_URL,
                    json={
                        "points": points,
                        "vehicle": VEHICLE,
                        "out_arrays": ["distances"],
                        "from_point": list(range(i_end - i)),
                        "to_point": list(range(i_end - i, len(points)))
                    },
                    headers={"Authorization": API_KEY}
                )
                response.raise_for_status()
                
                # Extract distances
                result = response.json()
                if 'distances' in result:
                    window_distances = result['distances']
                    distances[i:i_end, j:j_end] = window_distances
                
                logging.info(f"Processed window {i//WINDOW_SIZE + 1}-{j//WINDOW_SIZE + 1}")
                
                # Respect rate limit
                time.sleep(RATE_LIMIT)
                
            except requests.exceptions.RequestException as e:
                logging.error(f"API request failed: {e}")
                continue
    
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
    output_file = 'data/graphhopper_distance.csv'
    df.to_csv(output_file)
    logging.info(f"Successfully saved distances to {output_file}")

def main():
    try:
        # Read station data
        stations = read_stations()
        logging.info(f"Read {len(stations)} stations from data/stations.csv")
        
        # Calculate distances
        distances = calculate_distances(stations)
        
        # Save results
        save_distances(distances, stations)
            
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main() 