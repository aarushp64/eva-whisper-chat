"""
Data Analytics Processor

This module provides advanced data analytics capabilities:
1. Data extraction and cleaning
2. Statistical analysis
3. Time series analysis
4. Pattern recognition
5. Data visualization
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
import logging
from pathlib import Path
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose

# Add server directory to path to allow imports from other modules
server_dir = Path(__file__).resolve().parent.parent
import sys

if str(server_dir) not in sys.path:
    sys.path.append(str(server_dir))

# Import configuration
from config.advanced_features import DATA_ANALYTICS_CONFIG, is_feature_enabled

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base directories
BASE_DIR = server_dir
DATA_DIR = BASE_DIR / "data"
ANALYTICS_DIR = DATA_DIR / "analytics"
ANALYTICS_DIR.mkdir(exist_ok=True, parents=True)

class DataProcessor:
    """Class for processing and analyzing data"""
    
    def __init__(self):
        self.data_cache = {}  # Cache for processed data
    
    def load_data(self, data_source: Union[str, pd.DataFrame, List[Dict]], data_type: str = "json") -> pd.DataFrame:
        """
        Load data from various sources
        
        Args:
            data_source: Path to data file, DataFrame, or list of dictionaries
            data_type: Type of data source (json, csv, dataframe, list)
            
        Returns:
            Pandas DataFrame with loaded data
        """
        try:
            if data_type == "dataframe" and isinstance(data_source, pd.DataFrame):
                return data_source
            
            elif data_type == "list" and isinstance(data_source, list):
                return pd.DataFrame(data_source)
            
            elif data_type == "json" and isinstance(data_source, str):
                if os.path.exists(data_source):
                    return pd.read_json(data_source)
                else:
                    try:
                        # Try parsing as JSON string
                        data = json.loads(data_source)
                        return pd.DataFrame(data)
                    except:
                        raise ValueError("Invalid JSON source")
            
            elif data_type == "csv" and isinstance(data_source, str):
                if os.path.exists(data_source):
                    return pd.read_csv(data_source)
                else:
                    raise ValueError("CSV file not found")
            
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
                
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return pd.DataFrame()
    
    def clean_data(self, df: pd.DataFrame, options: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Clean and preprocess data
        
        Args:
            df: Input DataFrame
            options: Cleaning options (drop_na, fill_na, drop_duplicates, etc.)
            
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            return df
        
        if options is None:
            options = {
                "drop_na": False,
                "fill_na": True,
                "fill_method": "mean",  # mean, median, mode, value
                "fill_value": 0,
                "drop_duplicates": True,
                "convert_dates": True,
                "date_columns": [],
                "drop_columns": []
            }
        
        try:
            # Make a copy to avoid modifying the original
            cleaned_df = df.copy()
            
            # Drop specified columns
            if options.get("drop_columns"):
                cleaned_df = cleaned_df.drop(columns=options["drop_columns"], errors="ignore")
            
            # Handle missing values
            if options.get("drop_na"):
                cleaned_df = cleaned_df.dropna()
            elif options.get("fill_na"):
                fill_method = options.get("fill_method", "mean")
                fill_value = options.get("fill_value", 0)
                
                # Fill numeric columns
                numeric_cols = cleaned_df.select_dtypes(include=np.number).columns
                
                if fill_method == "mean":
                    cleaned_df[numeric_cols] = cleaned_df[numeric_cols].fillna(cleaned_df[numeric_cols].mean())
                elif fill_method == "median":
                    cleaned_df[numeric_cols] = cleaned_df[numeric_cols].fillna(cleaned_df[numeric_cols].median())
                elif fill_method == "mode":
                    for col in numeric_cols:
                        mode_value = cleaned_df[col].mode()
                        if not mode_value.empty:
                            cleaned_df[col] = cleaned_df[col].fillna(mode_value[0])
                else:
                    cleaned_df[numeric_cols] = cleaned_df[numeric_cols].fillna(fill_value)
                
                # Fill non-numeric columns with most frequent value
                non_numeric_cols = cleaned_df.select_dtypes(exclude=np.number).columns
                for col in non_numeric_cols:
                    mode_value = cleaned_df[col].mode()
                    if not mode_value.empty:
                        cleaned_df[col] = cleaned_df[col].fillna(mode_value[0])
            
            # Drop duplicates
            if options.get("drop_duplicates"):
                cleaned_df = cleaned_df.drop_duplicates()
            
            # Convert date columns
            if options.get("convert_dates") and options.get("date_columns"):
                for col in options["date_columns"]:
                    if col in cleaned_df.columns:
                        try:
                            cleaned_df[col] = pd.to_datetime(cleaned_df[col])
                        except:
                            logger.warning(f"Could not convert column {col} to datetime")
            
            return cleaned_df
            
        except Exception as e:
            logger.error(f"Error cleaning data: {str(e)}")
            return df
    
    def analyze_statistics(self, df: pd.DataFrame, columns: List[str] = None) -> Dict[str, Any]:
        """
        Perform statistical analysis on data
        
        Args:
            df: Input DataFrame
            columns: Columns to analyze (if None, analyze all numeric columns)
            
        Returns:
            Dictionary with statistical analysis results
        """
        if df.empty:
            return {}
        
        try:
            # Select columns to analyze
            if columns:
                analyze_cols = [col for col in columns if col in df.columns]
                analyze_df = df[analyze_cols]
            else:
                analyze_df = df.select_dtypes(include=np.number)
            
            if analyze_df.empty:
                return {}
            
            # Calculate statistics
            stats = {
                "summary": analyze_df.describe().to_dict(),
                "correlation": analyze_df.corr().to_dict(),
                "missing_values": analyze_df.isnull().sum().to_dict(),
                "column_types": {col: str(dtype) for col, dtype in analyze_df.dtypes.items()}
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error analyzing statistics: {str(e)}")
            return {}
    
    def perform_clustering(self, df: pd.DataFrame, columns: List[str], n_clusters: int = 3, method: str = "kmeans") -> Dict[str, Any]:
        """
        Perform clustering analysis
        
        Args:
            df: Input DataFrame
            columns: Columns to use for clustering
            n_clusters: Number of clusters (for KMeans)
            method: Clustering method (kmeans, dbscan)
            
        Returns:
            Dictionary with clustering results
        """
        if df.empty:
            return {}
        
        try:
            # Select columns for clustering
            cluster_cols = [col for col in columns if col in df.columns]
            if not cluster_cols:
                return {}
            
            cluster_data = df[cluster_cols].copy()
            
            # Handle missing values
            cluster_data = cluster_data.fillna(cluster_data.mean())
            
            # Standardize data
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(cluster_data)
            
            # Reduce dimensions for visualization
            pca = PCA(n_components=2)
            pca_result = pca.fit_transform(scaled_data)
            
            # Perform clustering
            if method == "kmeans":
                model = KMeans(n_clusters=n_clusters, random_state=42)
                clusters = model.fit_predict(scaled_data)
                centers = model.cluster_centers_
                
                # Transform centers to PCA space for visualization
                centers_pca = pca.transform(centers)
                
            elif method == "dbscan":
                model = DBSCAN(eps=0.5, min_samples=5)
                clusters = model.fit_predict(scaled_data)
                centers = None
                centers_pca = None
            
            else:
                raise ValueError(f"Unsupported clustering method: {method}")
            
            # Prepare results
            results = {
                "clusters": clusters.tolist(),
                "pca_data": pca_result.tolist(),
                "centers": centers_pca.tolist() if centers_pca is not None else None,
                "explained_variance": pca.explained_variance_ratio_.tolist(),
                "method": method,
                "n_clusters": len(set(clusters)) - (1 if -1 in clusters else 0)
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error performing clustering: {str(e)}")
            return {}
    
    def analyze_time_series(self, df: pd.DataFrame, date_column: str, value_column: str, period: str = "D") -> Dict[str, Any]:
        """
        Perform time series analysis
        
        Args:
            df: Input DataFrame
            date_column: Column containing dates
            value_column: Column containing values to analyze
            period: Resampling period (D=daily, W=weekly, M=monthly, etc.)
            
        Returns:
            Dictionary with time series analysis results
        """
        if df.empty or date_column not in df.columns or value_column not in df.columns:
            return {}
        
        try:
            # Convert date column to datetime if needed
            if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
                df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
            
            # Create time series
            ts_df = df[[date_column, value_column]].dropna()
            ts_df = ts_df.set_index(date_column)
            
            # Resample to regular intervals
            ts_resampled = ts_df[value_column].resample(period).mean()
            
            # Fill missing values in resampled data
            ts_resampled = ts_resampled.fillna(method="ffill")
            
            # Basic time series statistics
            stats = {
                "mean": ts_resampled.mean(),
                "std": ts_resampled.std(),
                "min": ts_resampled.min(),
                "max": ts_resampled.max(),
                "trend": "increasing" if ts_resampled.iloc[-1] > ts_resampled.iloc[0] else "decreasing"
            }
            
            # Decompose time series if enough data points
            if len(ts_resampled) >= 4:
                try:
                    # Decompose into trend, seasonal, and residual components
                    decomposition = seasonal_decompose(ts_resampled, model="additive", extrapolate_trend="freq")
                    
                    # Extract components
                    trend = decomposition.trend
                    seasonal = decomposition.seasonal
                    residual = decomposition.resid
                    
                    # Add decomposition to results
                    stats["decomposition"] = {
                        "trend": trend.dropna().tolist(),
                        "seasonal": seasonal.dropna().tolist(),
                        "residual": residual.dropna().tolist(),
                        "dates": trend.dropna().index.strftime("%Y-%m-%d").tolist()
                    }
                except:
                    logger.warning("Could not perform seasonal decomposition")
            
            # Simple forecast using ARIMA if enough data points
            if len(ts_resampled) >= 10:
                try:
                    # Fit ARIMA model
                    model = ARIMA(ts_resampled, order=(1, 1, 1))
                    model_fit = model.fit()
                    
                    # Forecast next 5 periods
                    forecast = model_fit.forecast(steps=5)
                    
                    # Add forecast to results
                    stats["forecast"] = {
                        "values": forecast.tolist(),
                        "dates": [
                            (ts_resampled.index[-1] + pd.Timedelta(f"{i+1}{period}")).strftime("%Y-%m-%d")
                            for i in range(len(forecast))
                        ]
                    }
                except:
                    logger.warning("Could not perform ARIMA forecast")
            
            # Prepare time series data for visualization
            stats["time_series"] = {
                "values": ts_resampled.tolist(),
                "dates": ts_resampled.index.strftime("%Y-%m-%d").tolist()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error analyzing time series: {str(e)}")
            return {}
    
    def generate_visualization(self, data: Dict[str, Any], viz_type: str = "line", title: str = "Data Visualization") -> str:
        """
        Generate data visualization
        
        Args:
            data: Data to visualize
            viz_type: Type of visualization (line, bar, scatter, pie, heatmap)
            title: Chart title
            
        Returns:
            Base64 encoded image of the visualization
        """
        try:
            plt.figure(figsize=(10, 6))
            
            if viz_type == "line":
                if "dates" in data and "values" in data:
                    plt.plot(data["dates"], data["values"])
                    plt.xticks(rotation=45)
                elif "x" in data and "y" in data:
                    plt.plot(data["x"], data["y"])
                else:
                    plt.plot(data.get("values", []))
                
                plt.title(title)
                plt.grid(True, linestyle="--", alpha=0.7)
                
            elif viz_type == "bar":
                if "categories" in data and "values" in data:
                    plt.bar(data["categories"], data["values"])
                    plt.xticks(rotation=45)
                else:
                    categories = data.get("categories", list(range(len(data.get("values", [])))))
                    plt.bar(categories, data.get("values", []))
                
                plt.title(title)
                
            elif viz_type == "scatter":
                if "x" in data and "y" in data:
                    # If clusters are provided, color by cluster
                    if "clusters" in data and len(data["clusters"]) == len(data["x"]):
                        unique_clusters = set(data["clusters"])
                        for cluster in unique_clusters:
                            mask = [c == cluster for c in data["clusters"]]
                            x_cluster = [data["x"][i] for i in range(len(data["x"])) if mask[i]]
                            y_cluster = [data["y"][i] for i in range(len(data["y"])) if mask[i]]
                            plt.scatter(x_cluster, y_cluster, label=f"Cluster {cluster}")
                        
                        # Plot cluster centers if available
                        if "centers" in data and data["centers"]:
                            centers_x = [center[0] for center in data["centers"]]
                            centers_y = [center[1] for center in data["centers"]]
                            plt.scatter(centers_x, centers_y, c="red", marker="x", s=100, label="Centroids")
                        
                        plt.legend()
                    else:
                        plt.scatter(data["x"], data["y"])
                
                plt.title(title)
                plt.grid(True, linestyle="--", alpha=0.7)
                
            elif viz_type == "pie":
                if "categories" in data and "values" in data:
                    plt.pie(data["values"], labels=data["categories"], autopct="%1.1f%%")
                else:
                    categories = data.get("categories", [f"Category {i+1}" for i in range(len(data.get("values", [])))])
                    plt.pie(data.get("values", []), labels=categories, autopct="%1.1f%%")
                
                plt.title(title)
                
            elif viz_type == "heatmap":
                if "matrix" in data:
                    plt.imshow(data["matrix"], cmap="viridis")
                    plt.colorbar()
                    
                    # Add row and column labels if available
                    if "row_labels" in data and "col_labels" in data:
                        plt.yticks(range(len(data["row_labels"])), data["row_labels"])
                        plt.xticks(range(len(data["col_labels"])), data["col_labels"], rotation=45)
                
                plt.title(title)
            
            else:
                raise ValueError(f"Unsupported visualization type: {viz_type}")
            
            # Save figure to BytesIO object
            buf = BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format="png")
            buf.seek(0)
            
            # Convert to base64
            img_str = base64.b64encode(buf.read()).decode("utf-8")
            plt.close()
            
            return img_str
            
        except Exception as e:
            logger.error(f"Error generating visualization: {str(e)}")
            return ""
    
    def extract_insights(self, df: pd.DataFrame, analysis_results: Dict[str, Any]) -> List[str]:
        """
        Extract insights from data analysis
        
        Args:
            df: Input DataFrame
            analysis_results: Results from various analyses
            
        Returns:
            List of insights as strings
        """
        insights = []
        
        try:
            # Check if we have data to analyze
            if df.empty or not analysis_results:
                return ["Not enough data to extract insights."]
            
            # Statistical insights
            if "summary" in analysis_results:
                summary = analysis_results["summary"]
                
                for col, stats in summary.items():
                    # Check for outliers
                    if "std" in stats and "mean" in stats:
                        std = stats["std"]
                        mean = stats["mean"]
                        max_val = stats.get("max")
                        min_val = stats.get("min")
                        
                        if max_val and max_val > mean + 2 * std:
                            insights.append(f"Column '{col}' has potential outliers above {mean + 2 * std:.2f}.")
                        
                        if min_val and min_val < mean - 2 * std:
                            insights.append(f"Column '{col}' has potential outliers below {mean - 2 * std:.2f}.")
                    
                    # Check for skewness
                    if "50%" in stats and "mean" in stats:
                        median = stats["50%"]
                        mean = stats["mean"]
                        
                        if mean > median * 1.1:
                            insights.append(f"Column '{col}' is positively skewed (mean > median).")
                        elif mean < median * 0.9:
                            insights.append(f"Column '{col}' is negatively skewed (mean < median).")
            
            # Correlation insights
            if "correlation" in analysis_results:
                correlation = analysis_results["correlation"]
                
                for col1, corr_values in correlation.items():
                    for col2, corr in corr_values.items():
                        if col1 != col2 and abs(corr) > 0.7:
                            direction = "positive" if corr > 0 else "negative"
                            insights.append(f"Strong {direction} correlation ({corr:.2f}) between '{col1}' and '{col2}'.")
            
            # Time series insights
            if "time_series" in analysis_results:
                ts_data = analysis_results["time_series"]
                
                if "trend" in analysis_results:
                    trend = analysis_results["trend"]
                    insights.append(f"The overall trend is {trend}.")
                
                if "forecast" in analysis_results:
                    forecast = analysis_results["forecast"]
                    last_value = ts_data["values"][-1] if ts_data["values"] else None
                    forecast_values = forecast.get("values", [])
                    
                    if last_value is not None and forecast_values:
                        last_forecast = forecast_values[-1]
                        change_pct = (last_forecast - last_value) / last_value * 100
                        
                        if change_pct > 10:
                            insights.append(f"Forecast shows a significant increase of {change_pct:.1f}% in the future.")
                        elif change_pct < -10:
                            insights.append(f"Forecast shows a significant decrease of {abs(change_pct):.1f}% in the future.")
                        else:
                            insights.append(f"Forecast shows a relatively stable trend with {change_pct:.1f}% change.")
            
            # Clustering insights
            if "clusters" in analysis_results:
                clusters = analysis_results["clusters"]
                n_clusters = analysis_results.get("n_clusters", len(set(clusters)))
                
                insights.append(f"Data can be grouped into {n_clusters} distinct clusters.")
                
                # Count elements in each cluster
                cluster_counts = {}
                for cluster in clusters:
                    if cluster != -1:  # Ignore noise points from DBSCAN
                        cluster_counts[cluster] = cluster_counts.get(cluster, 0) + 1
                
                # Find largest and smallest clusters
                if cluster_counts:
                    largest_cluster = max(cluster_counts, key=cluster_counts.get)
                    smallest_cluster = min(cluster_counts, key=cluster_counts.get)
                    
                    insights.append(f"Largest group is cluster {largest_cluster} with {cluster_counts[largest_cluster]} items.")
                    insights.append(f"Smallest group is cluster {smallest_cluster} with {cluster_counts[smallest_cluster]} items.")
            
            return insights
            
        except Exception as e:
            logger.error(f"Error extracting insights: {str(e)}")
            return ["Could not extract insights due to an error."]
    
    def process_data_request(self, data_source: Union[str, pd.DataFrame, List[Dict]], request_type: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a data analysis request
        
        Args:
            data_source: Data to analyze
            request_type: Type of analysis (statistics, clustering, time_series, visualization)
            options: Additional options for the analysis
            
        Returns:
            Dictionary with analysis results
        """
        if options is None:
            options = {}
        
        try:
            # Load and clean data
            data_type = options.get("data_type", "json")
            df = self.load_data(data_source, data_type)
            
            if df.empty:
                return {"error": "No data available for analysis"}
            
            # Clean data if requested
            if options.get("clean_data", True):
                cleaning_options = options.get("cleaning_options", {})
                df = self.clean_data(df, cleaning_options)
            
            # Process based on request type
            if request_type == "statistics":
                columns = options.get("columns")
                results = self.analyze_statistics(df, columns)
                
                # Extract insights if requested
                if options.get("extract_insights", True):
                    results["insights"] = self.extract_insights(df, results)
                
                return results
            
            elif request_type == "clustering":
                columns = options.get("columns", df.select_dtypes(include=np.number).columns.tolist())
                n_clusters = options.get("n_clusters", 3)
                method = options.get("method", "kmeans")
                
                results = self.perform_clustering(df, columns, n_clusters, method)
                
                # Generate visualization if requested
                if options.get("visualize", True):
                    viz_data = {
                        "x": [point[0] for point in results.get("pca_data", [])],
                        "y": [point[1] for point in results.get("pca_data", [])],
                        "clusters": results.get("clusters", []),
                        "centers": results.get("centers")
                    }
                    
                    viz_title = options.get("viz_title", f"Clustering Results ({method})")
                    viz_type = "scatter"
                    
                    results["visualization"] = self.generate_visualization(viz_data, viz_type, viz_title)
                
                # Extract insights if requested
                if options.get("extract_insights", True):
                    results["insights"] = self.extract_insights(df, results)
                
                return results
            
            elif request_type == "time_series":
                date_column = options.get("date_column")
                value_column = options.get("value_column")
                period = options.get("period", "D")
                
                if not date_column or not value_column:
                    return {"error": "Date and value columns must be specified for time series analysis"}
                
                results = self.analyze_time_series(df, date_column, value_column, period)
                
                # Generate visualization if requested
                if options.get("visualize", True):
                    viz_data = results.get("time_series", {})
                    
                    # Add forecast if available
                    if "forecast" in results:
                        viz_data["forecast_values"] = results["forecast"]["values"]
                        viz_data["forecast_dates"] = results["forecast"]["dates"]
                    
                    viz_title = options.get("viz_title", f"Time Series Analysis: {value_column}")
                    viz_type = "line"
                    
                    results["visualization"] = self.generate_visualization(viz_data, viz_type, viz_title)
                
                # Extract insights if requested
                if options.get("extract_insights", True):
                    results["insights"] = self.extract_insights(df, results)
                
                return results
            
            elif request_type == "visualization":
                viz_type = options.get("viz_type", "line")
                viz_title = options.get("viz_title", "Data Visualization")
                
                # Prepare data for visualization
                viz_data = {}
                
                if viz_type == "line":
                    x_column = options.get("x_column")
                    y_column = options.get("y_column")
                    
                    if x_column and y_column:
                        viz_data["x"] = df[x_column].tolist()
                        viz_data["y"] = df[y_column].tolist()
                    elif y_column:
                        viz_data["values"] = df[y_column].tolist()
                    
                elif viz_type == "bar":
                    category_column = options.get("category_column")
                    value_column = options.get("value_column")
                    
                    if category_column and value_column:
                        viz_data["categories"] = df[category_column].tolist()
                        viz_data["values"] = df[value_column].tolist()
                    
                elif viz_type == "scatter":
                    x_column = options.get("x_column")
                    y_column = options.get("y_column")
                    
                    if x_column and y_column:
                        viz_data["x"] = df[x_column].tolist()
                        viz_data["y"] = df[y_column].tolist()
                    
                elif viz_type == "pie":
                    category_column = options.get("category_column")
                    value_column = options.get("value_column")
                    
                    if category_column and value_column:
                        viz_data["categories"] = df[category_column].tolist()
                        viz_data["values"] = df[value_column].tolist()
                    
                elif viz_type == "heatmap":
                    pivot_index = options.get("pivot_index")
                    pivot_columns = options.get("pivot_columns")
                    pivot_values = options.get("pivot_values")
                    
                    if pivot_index and pivot_columns and pivot_values:
                        pivot_table = df.pivot(index=pivot_index, columns=pivot_columns, values=pivot_values)
                        viz_data["matrix"] = pivot_table.values.tolist()
                        viz_data["row_labels"] = pivot_table.index.tolist()
                        viz_data["col_labels"] = pivot_table.columns.tolist()
                
                # Generate visualization
                visualization = self.generate_visualization(viz_data, viz_type, viz_title)
                
                return {
                    "visualization": visualization,
                    "viz_type": viz_type,
                    "viz_title": viz_title
                }
            
            else:
                return {"error": f"Unsupported request type: {request_type}"}
            
        except Exception as e:
            logger.error(f"Error processing data request: {str(e)}")
            return {"error": f"Error processing data request: {str(e)}"}

# Create a global instance
data_processor = DataProcessor()

def get_data_processor() -> DataProcessor:
    """Get the global data processor instance"""
    return data_processor
