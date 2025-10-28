import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from datetime import datetime
import os
import json

class DataProcessor:
    """Class for data processing and analysis"""
    
    def __init__(self):
        self.data = None
        self.data_info = None
        self.analysis_results = {}
    
    def load_data(self, file_path=None, data=None, file_type=None):
        """
        Load data from file or dataframe
        
        Args:
            file_path (str): Path to data file
            data (pandas.DataFrame): DataFrame to use
            file_type (str): Type of file (csv, excel, json)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if data is not None:
                # Use provided dataframe
                self.data = data
            elif file_path is not None:
                # Determine file type if not provided
                if file_type is None:
                    if file_path.endswith('.csv'):
                        file_type = 'csv'
                    elif file_path.endswith(('.xls', '.xlsx')):
                        file_type = 'excel'
                    elif file_path.endswith('.json'):
                        file_type = 'json'
                    else:
                        return False
                
                # Load data based on file type
                if file_type == 'csv':
                    self.data = pd.read_csv(file_path)
                elif file_type == 'excel':
                    self.data = pd.read_excel(file_path)
                elif file_type == 'json':
                    self.data = pd.read_json(file_path)
                else:
                    return False
            else:
                return False
            
            # Generate data info
            self._generate_data_info()
            
            return True
        except Exception as e:
            print(f"Error loading data: {str(e)}")
            return False
    
    def _generate_data_info(self):
        """Generate basic information about the data"""
        if self.data is None:
            return
        
        # Basic info
        self.data_info = {
            "rows": len(self.data),
            "columns": len(self.data.columns),
            "column_names": list(self.data.columns),
            "column_types": {col: str(dtype) for col, dtype in self.data.dtypes.items()},
            "missing_values": self.data.isnull().sum().to_dict(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Add column statistics for numeric columns
        numeric_columns = self.data.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) > 0:
            self.data_info["numeric_stats"] = self.data[numeric_columns].describe().to_dict()
    
    def get_data_info(self):
        """Get information about the loaded data"""
        return self.data_info
    
    def analyze_data(self, analysis_type="basic"):
        """
        Perform data analysis
        
        Args:
            analysis_type (str): Type of analysis to perform
            
        Returns:
            dict: Analysis results
        """
        if self.data is None:
            return None
        
        try:
            if analysis_type == "basic":
                # Basic statistical analysis
                result = self._basic_analysis()
            elif analysis_type == "correlation":
                # Correlation analysis
                result = self._correlation_analysis()
            elif analysis_type == "time_series":
                # Time series analysis
                result = self._time_series_analysis()
            elif analysis_type == "categorical":
                # Categorical data analysis
                result = self._categorical_analysis()
            else:
                return None
            
            # Store results
            self.analysis_results[analysis_type] = result
            
            return result
        except Exception as e:
            print(f"Error analyzing data: {str(e)}")
            return None
    
    def _basic_analysis(self):
        """Perform basic statistical analysis"""
        # Get numeric columns
        numeric_columns = self.data.select_dtypes(include=[np.number]).columns
        
        if len(numeric_columns) == 0:
            return {"error": "No numeric columns found"}
        
        # Calculate basic statistics
        stats = self.data[numeric_columns].describe()
        
        # Calculate additional statistics
        skewness = self.data[numeric_columns].skew()
        kurtosis = self.data[numeric_columns].kurtosis()
        
        # Format results
        result = {
            "statistics": stats.to_dict(),
            "skewness": skewness.to_dict(),
            "kurtosis": kurtosis.to_dict()
        }
        
        return result
    
    def _correlation_analysis(self):
        """Perform correlation analysis"""
        # Get numeric columns
        numeric_columns = self.data.select_dtypes(include=[np.number]).columns
        
        if len(numeric_columns) < 2:
            return {"error": "Not enough numeric columns for correlation analysis"}
        
        # Calculate correlation matrix
        corr_matrix = self.data[numeric_columns].corr()
        
        # Format results
        result = {
            "correlation_matrix": corr_matrix.to_dict(),
            "high_correlations": []
        }
        
        # Find high correlations
        for i in range(len(numeric_columns)):
            for j in range(i+1, len(numeric_columns)):
                col1 = numeric_columns[i]
                col2 = numeric_columns[j]
                corr = corr_matrix.iloc[i, j]
                
                if abs(corr) > 0.5:
                    result["high_correlations"].append({
                        "column1": col1,
                        "column2": col2,
                        "correlation": corr
                    })
        
        return result
    
    def _time_series_analysis(self):
        """Perform time series analysis"""
        # Check if there's a datetime column
        datetime_columns = []
        for col in self.data.columns:
            try:
                pd.to_datetime(self.data[col])
                datetime_columns.append(col)
            except:
                pass
        
        if len(datetime_columns) == 0:
            return {"error": "No datetime columns found"}
        
        # Use the first datetime column
        date_col = datetime_columns[0]
        
        # Convert to datetime
        self.data[date_col] = pd.to_datetime(self.data[date_col])
        
        # Get numeric columns
        numeric_columns = self.data.select_dtypes(include=[np.number]).columns
        
        if len(numeric_columns) == 0:
            return {"error": "No numeric columns found"}
        
        # Resample data by day, week, and month
        result = {
            "datetime_column": date_col,
            "numeric_columns": list(numeric_columns),
            "daily": {},
            "weekly": {},
            "monthly": {}
        }
        
        # Set date as index
        df_time = self.data.set_index(date_col)
        
        # Resample for each numeric column
        for col in numeric_columns:
            # Daily
            daily = df_time[col].resample('D').mean()
            result["daily"][col] = {
                "dates": [d.strftime("%Y-%m-%d") for d in daily.index],
                "values": daily.values.tolist()
            }
            
            # Weekly
            weekly = df_time[col].resample('W').mean()
            result["weekly"][col] = {
                "dates": [d.strftime("%Y-%m-%d") for d in weekly.index],
                "values": weekly.values.tolist()
            }
            
            # Monthly
            monthly = df_time[col].resample('M').mean()
            result["monthly"][col] = {
                "dates": [d.strftime("%Y-%m-%d") for d in monthly.index],
                "values": monthly.values.tolist()
            }
        
        return result
    
    def _categorical_analysis(self):
        """Perform categorical data analysis"""
        # Get categorical columns
        categorical_columns = self.data.select_dtypes(include=['object', 'category']).columns
        
        if len(categorical_columns) == 0:
            return {"error": "No categorical columns found"}
        
        result = {
            "categorical_columns": list(categorical_columns),
            "value_counts": {},
            "cross_tabs": {}
        }
        
        # Calculate value counts for each categorical column
        for col in categorical_columns:
            counts = self.data[col].value_counts()
            result["value_counts"][col] = {
                "values": counts.index.tolist(),
                "counts": counts.values.tolist()
            }
        
        # Calculate cross-tabulations for pairs of categorical columns
        if len(categorical_columns) >= 2:
            for i in range(len(categorical_columns)):
                for j in range(i+1, len(categorical_columns)):
                    col1 = categorical_columns[i]
                    col2 = categorical_columns[j]
                    
                    cross_tab = pd.crosstab(self.data[col1], self.data[col2])
                    result["cross_tabs"][f"{col1}_vs_{col2}"] = cross_tab.to_dict()
        
        return result
    
    def generate_visualization(self, viz_type, columns=None, **kwargs):
        """
        Generate data visualization
        
        Args:
            viz_type (str): Type of visualization
            columns (list): Columns to include
            **kwargs: Additional parameters
            
        Returns:
            str: Base64-encoded image
        """
        if self.data is None:
            return None
        
        try:
            plt.figure(figsize=(10, 6))
            
            if viz_type == "histogram":
                return self._generate_histogram(columns, **kwargs)
            elif viz_type == "scatter":
                return self._generate_scatter(columns, **kwargs)
            elif viz_type == "line":
                return self._generate_line(columns, **kwargs)
            elif viz_type == "bar":
                return self._generate_bar(columns, **kwargs)
            elif viz_type == "box":
                return self._generate_box(columns, **kwargs)
            elif viz_type == "heatmap":
                return self._generate_heatmap(**kwargs)
            else:
                return None
        except Exception as e:
            print(f"Error generating visualization: {str(e)}")
            return None
    
    def _generate_histogram(self, columns, bins=10, kde=True):
        """Generate histogram"""
        if columns is None:
            # Use numeric columns
            columns = self.data.select_dtypes(include=[np.number]).columns[:3]
        
        for col in columns:
            sns.histplot(self.data[col], bins=bins, kde=kde, label=col)
        
        plt.title("Histogram")
        plt.legend()
        
        return self._fig_to_base64()
    
    def _generate_scatter(self, columns, hue=None):
        """Generate scatter plot"""
        if columns is None or len(columns) < 2:
            # Use first two numeric columns
            numeric_cols = self.data.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) < 2:
                return None
            columns = numeric_cols[:2]
        
        sns.scatterplot(x=columns[0], y=columns[1], data=self.data, hue=hue)
        plt.title(f"Scatter Plot: {columns[0]} vs {columns[1]}")
        
        return self._fig_to_base64()
    
    def _generate_line(self, columns, x=None):
        """Generate line plot"""
        if x is None:
            # Try to find a datetime column
            for col in self.data.columns:
                try:
                    self.data[col] = pd.to_datetime(self.data[col])
                    x = col
                    break
                except:
                    pass
        
        if columns is None:
            # Use numeric columns
            columns = self.data.select_dtypes(include=[np.number]).columns[:3]
        
        if x is not None:
            for col in columns:
                plt.plot(self.data[x], self.data[col], label=col)
            plt.xlabel(x)
        else:
            for col in columns:
                plt.plot(self.data[col], label=col)
        
        plt.title("Line Plot")
        plt.legend()
        
        return self._fig_to_base64()
    
    def _generate_bar(self, columns, x=None, stacked=False):
        """Generate bar plot"""
        if columns is None:
            # Use categorical columns
            columns = self.data.select_dtypes(include=['object', 'category']).columns[:1]
            if len(columns) == 0:
                # Use numeric columns
                columns = self.data.select_dtypes(include=[np.number]).columns[:1]
        
        if len(columns) == 1:
            # Single column bar plot
            counts = self.data[columns[0]].value_counts()
            plt.bar(counts.index, counts.values)
            plt.title(f"Bar Plot: {columns[0]}")
            plt.xticks(rotation=45)
        elif x is not None:
            # Multiple columns with x-axis
            if stacked:
                self.data[columns].plot(kind='bar', stacked=True, x=x)
            else:
                self.data[columns].plot(kind='bar', x=x)
            plt.title(f"Bar Plot by {x}")
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        return self._fig_to_base64()
    
    def _generate_box(self, columns, by=None):
        """Generate box plot"""
        if columns is None:
            # Use numeric columns
            columns = self.data.select_dtypes(include=[np.number]).columns
        
        if by is not None:
            # Box plot grouped by a categorical variable
            sns.boxplot(x=by, y=columns[0], data=self.data)
            plt.title(f"Box Plot: {columns[0]} by {by}")
            plt.xticks(rotation=45)
        else:
            # Box plot for multiple columns
            sns.boxplot(data=self.data[columns])
            plt.title("Box Plot")
        
        plt.tight_layout()
        return self._fig_to_base64()
    
    def _generate_heatmap(self, **kwargs):
        """Generate correlation heatmap"""
        # Get numeric columns
        numeric_columns = self.data.select_dtypes(include=[np.number]).columns
        
        if len(numeric_columns) < 2:
            return None
        
        # Calculate correlation matrix
        corr_matrix = self.data[numeric_columns].corr()
        
        # Generate heatmap
        sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", linewidths=0.5)
        plt.title("Correlation Heatmap")
        plt.tight_layout()
        
        return self._fig_to_base64()
    
    def _fig_to_base64(self):
        """Convert matplotlib figure to base64 string"""
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        return img_str
    
    def natural_language_query(self, query):
        """
        Process a natural language query about the data
        
        Args:
            query (str): Natural language query
            
        Returns:
            dict: Query results
        """
        if self.data is None:
            return {"error": "No data loaded"}
        
        # This is a simple implementation that handles basic queries
        # A more sophisticated implementation would use NLP techniques
        
        query = query.lower()
        result = {"query": query, "type": "unknown", "result": None}
        
        # Check for column names in the query
        columns_in_query = []
        for col in self.data.columns:
            if col.lower() in query:
                columns_in_query.append(col)
        
        # Handle different types of queries
        if "average" in query or "mean" in query:
            result["type"] = "average"
            if columns_in_query:
                result["result"] = {col: float(self.data[col].mean()) for col in columns_in_query}
            else:
                # If no specific columns mentioned, return mean of all numeric columns
                numeric_cols = self.data.select_dtypes(include=[np.number]).columns
                result["result"] = {col: float(self.data[col].mean()) for col in numeric_cols}
        
        elif "sum" in query or "total" in query:
            result["type"] = "sum"
            if columns_in_query:
                result["result"] = {col: float(self.data[col].sum()) for col in columns_in_query}
            else:
                # If no specific columns mentioned, return sum of all numeric columns
                numeric_cols = self.data.select_dtypes(include=[np.number]).columns
                result["result"] = {col: float(self.data[col].sum()) for col in numeric_cols}
        
        elif "maximum" in query or "max" in query:
            result["type"] = "max"
            if columns_in_query:
                result["result"] = {col: float(self.data[col].max()) for col in columns_in_query}
            else:
                # If no specific columns mentioned, return max of all numeric columns
                numeric_cols = self.data.select_dtypes(include=[np.number]).columns
                result["result"] = {col: float(self.data[col].max()) for col in numeric_cols}
        
        elif "minimum" in query or "min" in query:
            result["type"] = "min"
            if columns_in_query:
                result["result"] = {col: float(self.data[col].min()) for col in columns_in_query}
            else:
                # If no specific columns mentioned, return min of all numeric columns
                numeric_cols = self.data.select_dtypes(include=[np.number]).columns
                result["result"] = {col: float(self.data[col].min()) for col in numeric_cols}
        
        elif "count" in query:
            result["type"] = "count"
            if columns_in_query:
                result["result"] = {col: self.data[col].value_counts().to_dict() for col in columns_in_query}
            else:
                # If no specific columns mentioned, return counts of all categorical columns
                cat_cols = self.data.select_dtypes(include=['object', 'category']).columns
                result["result"] = {col: self.data[col].value_counts().to_dict() for col in cat_cols}
        
        elif "correlation" in query or "correlate" in query:
            result["type"] = "correlation"
            if len(columns_in_query) >= 2:
                result["result"] = {
                    "correlation": float(self.data[columns_in_query[0]].corr(self.data[columns_in_query[1]])),
                    "column1": columns_in_query[0],
                    "column2": columns_in_query[1]
                }
            else:
                # If no specific columns mentioned, return correlation matrix
                numeric_cols = self.data.select_dtypes(include=[np.number]).columns
                result["result"] = self.data[numeric_cols].corr().to_dict()
        
        elif "trend" in query or "over time" in query:
            result["type"] = "trend"
            # Try to find a datetime column
            datetime_col = None
            for col in self.data.columns:
                try:
                    pd.to_datetime(self.data[col])
                    datetime_col = col
                    break
                except:
                    pass
            
            if datetime_col and columns_in_query:
                # Convert to datetime
                self.data[datetime_col] = pd.to_datetime(self.data[datetime_col])
                
                # Set datetime as index
                df_time = self.data.set_index(datetime_col)
                
                # Resample by month
                monthly = df_time[columns_in_query].resample('M').mean()
                
                result["result"] = {
                    "datetime_column": datetime_col,
                    "columns": columns_in_query,
                    "dates": [d.strftime("%Y-%m-%d") for d in monthly.index],
                    "values": {col: monthly[col].values.tolist() for col in columns_in_query}
                }
            else:
                result["result"] = {"error": "No datetime column or target columns found"}
        
        else:
            # For unknown queries, return basic statistics
            result["type"] = "statistics"
            if columns_in_query:
                result["result"] = {col: self.data[col].describe().to_dict() for col in columns_in_query}
            else:
                # If no specific columns mentioned, return statistics of all columns
                result["result"] = self.data.describe().to_dict()
        
        return result
    
    def save_analysis(self, directory="analysis_results"):
        """
        Save analysis results to disk
        
        Args:
            directory (str): Directory to save results to
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.analysis_results:
            return False
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(directory, exist_ok=True)
            
            # Save data info
            if self.data_info:
                with open(f"{directory}/data_info.json", "w") as f:
                    json.dump(self.data_info, f, indent=2)
            
            # Save analysis results
            for analysis_type, result in self.analysis_results.items():
                with open(f"{directory}/{analysis_type}_analysis.json", "w") as f:
                    json.dump(result, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving analysis: {str(e)}")
            return False
