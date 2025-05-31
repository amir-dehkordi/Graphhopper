import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# Create results directory if it doesn't exist
os.makedirs('results', exist_ok=True)

# Read the CSV files
try:
    network_dist = pd.read_csv('data/graphhopper_distance.csv')
    geopy_dist = pd.read_csv('data/geopy_distance.csv')
except FileNotFoundError as e:
    print(f"Error: Could not find required input files: {e}")
    print("Please make sure both distance calculation scripts have been run first.")
    sys.exit(1)

# Validate data
if network_dist.shape != geopy_dist.shape:
    print("Error: The distance matrices have different shapes!")
    print(f"GraphHopper matrix shape: {network_dist.shape}")
    print(f"Geopy matrix shape: {geopy_dist.shape}")
    sys.exit(1)

# Convert to numpy arrays for easier calculation
network_array = network_dist.values
geopy_array = geopy_dist.values

# Calculate differences
differences = network_array - geopy_array

# Validate differences
if np.all(np.isnan(differences)):
    print("Error: All differences are NaN. Please check the input data.")
    sys.exit(1)

# Perform paired t-test
# We'll use the differences between corresponding elements
# Flatten the arrays to get all pairs
network_flat = network_array.flatten()
geopy_flat = geopy_array.flatten()

# Remove any NaN values if they exist
mask = ~(np.isnan(network_flat) | np.isnan(geopy_flat))
network_flat = network_flat[mask]
geopy_flat = geopy_flat[mask]

if len(network_flat) == 0:
    print("Error: No valid data points after removing NaN values.")
    sys.exit(1)

# Perform the paired t-test
t_stat, p_value = stats.ttest_rel(network_flat, geopy_flat)

# Calculate some basic statistics
mean_diff = np.mean(differences)
std_diff = np.std(differences)
median_diff = np.median(differences)

# Print results
print("\nStatistical Analysis Results:")
print(f"Number of station pairs: {len(network_flat)}")
print(f"Mean difference (Network - Geodesic): {mean_diff:.2f} meters")
print(f"Standard deviation of differences: {std_diff:.2f} meters")
print(f"Median difference: {median_diff:.2f} meters")
print(f"\nPaired t-test results:")
print(f"t-statistic: {t_stat:.4f}")
print(f"p-value: {p_value:.10f}")

# Create individual high-resolution plots
plt.rcParams['figure.dpi'] = 400

# Save plot settings
plot_settings = {
    'dpi': 400,
    'bbox_inches': 'tight',
    'facecolor': 'white'
}

# 1. Histogram of differences
plt.figure(figsize=(10, 8))
plt.hist(differences.flatten(), bins=50, color='skyblue', edgecolor='black')
plt.title('Distribution of Distance Differences', fontsize=14, pad=20)
plt.xlabel('Difference (Network - Geodesic) in meters', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.grid(True, alpha=0.3)
plt.savefig('results/histogram_differences.png', **plot_settings)
plt.close()

# 2. Box plot of differences
plt.figure(figsize=(10, 8))
plt.boxplot(differences.flatten(), patch_artist=True)
plt.title('Box Plot of Distance Differences', fontsize=14, pad=20)
plt.ylabel('Difference (Network - Geodesic) in meters', fontsize=12)
plt.grid(True, alpha=0.3)
plt.savefig('results/boxplot_differences.png', **plot_settings)
plt.close()

# 3. Scatter plot of Network vs Geodesic distances
plt.figure(figsize=(10, 8))
plt.scatter(geopy_flat, network_flat, alpha=0.1, color='blue')
plt.plot([0, max(geopy_flat)], [0, max(geopy_flat)], 'r--', label='Perfect correlation')
plt.title('Network vs Geodesic Distances', fontsize=14, pad=20)
plt.xlabel('Geodesic Distance (meters)', fontsize=12)
plt.ylabel('Network Distance (meters)', fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend()
plt.savefig('results/scatter_comparison.png', **plot_settings)
plt.close()

# 4. QQ plot of differences
plt.figure(figsize=(10, 8))
stats.probplot(differences.flatten(), dist="norm", plot=plt)
plt.title('Q-Q Plot of Differences', fontsize=14, pad=20)
plt.grid(True, alpha=0.3)
plt.savefig('results/qqplot_differences.png', **plot_settings)
plt.close()

# Additional analysis: Calculate percentage of cases where network distance is longer
network_longer = np.sum(differences > 0)
total_pairs = np.sum(~np.isnan(differences))
percentage_longer = (network_longer / total_pairs) * 100

print(f"\nAdditional Analysis:")
print(f"Percentage of cases where network distance is longer: {percentage_longer:.2f}%")

# Save summary statistics to a text file
with open('results/analysis_summary.txt', 'w') as f:
    f.write("Distance Analysis Summary\n")
    f.write("=======================\n\n")
    f.write(f"Number of station pairs: {len(network_flat)}\n")
    f.write(f"Mean difference (Network - Geodesic): {mean_diff:.2f} meters\n")
    f.write(f"Standard deviation of differences: {std_diff:.2f} meters\n")
    f.write(f"Median difference: {median_diff:.2f} meters\n\n")
    f.write("Paired t-test results:\n")
    f.write(f"t-statistic: {t_stat:.4f}\n")
    f.write(f"p-value: {p_value:.10f}\n\n")
    f.write(f"Percentage of cases where network distance is longer: {percentage_longer:.2f}%\n")