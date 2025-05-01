import time
import numpy as np
import pandas as pd
import requests
import os
from typing import List, Tuple
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
            origins = self.extract_coordinates(data, origin_idx[0], origin_idx[1])
            
            for destination_idx in indices:
                destinations = self.extract_coordinates(data, destination_idx[0], destination_idx[1])
                
                try:
                    response = self._make_api_request(origins, destinations)
                    results = np.array(response["distances"])
                    
                    final_result[origin_idx[0]:origin_idx[1], 
                               destination_idx[0]:destination_idx[1]] = results
                    
                    logger.info(f"Processed: From {origin_idx} To {destination_idx}")
                    
                except Exception as e:
                    logger.error(f"Error processing batch {origin_idx} to {destination_idx}: {str(e)}")
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

def main():
    # Load data
    try:
        data = pd.read_csv("202306.csv")
        data = data[["ID", "lat", "lon"]]
        data = data.values
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        return
    
    # Initialize calculator
    api_key = os.getenv("GRAPHHOPPER_API_KEY")
    if not api_key:
        logger.error("GRAPHHOPPER_API_KEY environment variable not set")
        return
    
    calculator = BikeStationDistanceCalculator(api_key)
    
    # Calculate distances
    try:
        distances = calculator.calculate_distances(data)
        
        # Save results
        df = pd.DataFrame(distances)
        df.to_csv("bike_station_distances.csv", index=False)
        logger.info("Successfully saved distances to bike_station_distances.csv")
        
    except Exception as e:
        logger.error(f"Error calculating distances: {str(e)}")

if __name__ == "__main__":
    main() 