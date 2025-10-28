"""
Machine Learning Processor

This module provides advanced machine learning capabilities:
1. User personalization
2. Predictive analytics
3. Pattern recognition
4. Recommendation systems
5. Anomaly detection
"""

import os
import json
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Union, Tuple
import logging
from pathlib import Path
import pickle
import joblib
from datetime import datetime
import sys

# ML libraries
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, IsolationForest
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline

# Add server directory to path to allow imports from other modules
server_dir = Path(__file__).resolve().parent.parent
if str(server_dir) not in sys.path:
    sys.path.append(str(server_dir))

# Import configuration
from config.advanced_features import ML_CONFIG, is_feature_enabled

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Base directories
BASE_DIR = server_dir
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = DATA_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True, parents=True)

class MLProcessor:
    """Class for machine learning processing and model management"""
    
    def __init__(self):
        self.models = {}  # Loaded models
        self.vectorizers = {}  # Text vectorizers
        self.scalers = {}  # Data scalers
        self.encoders = {}  # Label encoders
        
        # Load available models
        self._load_available_models()
    
    def _load_available_models(self) -> None:
        """Load available models from disk"""
        try:
            # Check for model files
            for model_file in MODELS_DIR.glob("*.joblib"):
                model_name = model_file.stem
                try:
                    self.models[model_name] = joblib.load(model_file)
                    logger.info(f"Loaded model: {model_name}")
                except Exception as e:
                    logger.error(f"Error loading model {model_name}: {str(e)}")
            
            # Load vectorizers
            vectorizer_dir = MODELS_DIR / "vectorizers"
            if vectorizer_dir.exists():
                for vec_file in vectorizer_dir.glob("*.joblib"):
                    vec_name = vec_file.stem
                    try:
                        self.vectorizers[vec_name] = joblib.load(vec_file)
                        logger.info(f"Loaded vectorizer: {vec_name}")
                    except Exception as e:
                        logger.error(f"Error loading vectorizer {vec_name}: {str(e)}")
            
            # Load scalers
            scaler_dir = MODELS_DIR / "scalers"
            if scaler_dir.exists():
                for scaler_file in scaler_dir.glob("*.joblib"):
                    scaler_name = scaler_file.stem
                    try:
                        self.scalers[scaler_name] = joblib.load(scaler_file)
                        logger.info(f"Loaded scaler: {scaler_name}")
                    except Exception as e:
                        logger.error(f"Error loading scaler {scaler_name}: {str(e)}")
            
            # Load encoders
            encoder_dir = MODELS_DIR / "encoders"
            if encoder_dir.exists():
                for encoder_file in encoder_dir.glob("*.joblib"):
                    encoder_name = encoder_file.stem
                    try:
                        self.encoders[encoder_name] = joblib.load(encoder_file)
                        logger.info(f"Loaded encoder: {encoder_name}")
                    except Exception as e:
                        logger.error(f"Error loading encoder {encoder_name}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
    
    def save_model(self, model, model_name: str, model_type: str = "model", metadata: Dict[str, Any] = None) -> bool:
        """
        Save a model to disk
        
        Args:
            model: Model to save
            model_name: Name of the model
            model_type: Type of model (model, vectorizer, scaler, encoder)
            metadata: Additional metadata about the model
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine save directory based on model type
            if model_type == "vectorizer":
                save_dir = MODELS_DIR / "vectorizers"
                self.vectorizers[model_name] = model
            elif model_type == "scaler":
                save_dir = MODELS_DIR / "scalers"
                self.scalers[model_name] = model
            elif model_type == "encoder":
                save_dir = MODELS_DIR / "encoders"
                self.encoders[model_name] = model
            else:
                save_dir = MODELS_DIR
                self.models[model_name] = model
            
            # Create directory if it doesn't exist
            save_dir.mkdir(exist_ok=True, parents=True)
            
            # Save model
            model_path = save_dir / f"{model_name}.joblib"
            joblib.dump(model, model_path)
            
            # Save metadata if provided
            if metadata:
                metadata_path = save_dir / f"{model_name}_metadata.json"
                with open(metadata_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2)
            
            logger.info(f"Saved {model_type} '{model_name}' to {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving {model_type} '{model_name}': {str(e)}")
            return False
    
    def train_classifier(
        self, 
        X_train: Union[np.ndarray, pd.DataFrame], 
        y_train: Union[np.ndarray, pd.Series],
        model_type: str = "random_forest",
        model_params: Dict[str, Any] = None,
        model_name: str = None,
        save_model: bool = True,
        preprocess: bool = True,
        text_features: List[str] = None
    ) -> Dict[str, Any]:
        """
        Train a classification model
        
        Args:
            X_train: Training features
            y_train: Training labels
            model_type: Type of model to train
            model_params: Parameters for the model
            model_name: Name to save the model as
            save_model: Whether to save the model
            preprocess: Whether to preprocess the data
            text_features: List of column names containing text data
            
        Returns:
            Dictionary with training results
        """
        try:
            # Convert to DataFrame if numpy array
            if isinstance(X_train, np.ndarray):
                X_train = pd.DataFrame(X_train)
            
            # Default model parameters
            if model_params is None:
                model_params = {}
            
            # Generate model name if not provided
            if model_name is None:
                model_name = f"classifier_{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Preprocess data if requested
            preprocessors = {}
            if preprocess:
                X_train, preprocessors = self._preprocess_data(X_train, text_features)
                
                # Save preprocessors
                for name, processor in preprocessors.items():
                    processor_type = name.split("_")[0]  # e.g., "scaler", "vectorizer"
                    self.save_model(processor, f"{model_name}_{name}", processor_type)
            
            # Create model based on type
            if model_type == "random_forest":
                model = RandomForestClassifier(**model_params)
            elif model_type == "logistic_regression":
                model = LogisticRegression(**model_params)
            elif model_type == "svm":
                model = SVC(**model_params)
            elif model_type == "knn":
                model = KNeighborsClassifier(**model_params)
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
            
            # Train model
            model.fit(X_train, y_train)
            
            # Evaluate model
            train_predictions = model.predict(X_train)
            train_accuracy = accuracy_score(y_train, train_predictions)
            
            # Calculate additional metrics if binary classification
            additional_metrics = {}
            if len(np.unique(y_train)) == 2:
                additional_metrics["precision"] = precision_score(y_train, train_predictions, average="binary")
                additional_metrics["recall"] = recall_score(y_train, train_predictions, average="binary")
                additional_metrics["f1"] = f1_score(y_train, train_predictions, average="binary")
            
            # Save model if requested
            if save_model:
                metadata = {
                    "model_type": model_type,
                    "model_params": model_params,
                    "train_accuracy": train_accuracy,
                    "additional_metrics": additional_metrics,
                    "preprocessors": list(preprocessors.keys()),
                    "created_at": datetime.now().isoformat(),
                    "feature_names": X_train.columns.tolist() if hasattr(X_train, "columns") else None,
                    "n_features": X_train.shape[1],
                    "n_samples": X_train.shape[0]
                }
                
                self.save_model(model, model_name, "model", metadata)
            
            # Return results
            return {
                "model": model,
                "model_name": model_name,
                "train_accuracy": train_accuracy,
                "additional_metrics": additional_metrics,
                "preprocessors": preprocessors
            }
            
        except Exception as e:
            logger.error(f"Error training classifier: {str(e)}")
            return {"error": str(e)}
    
    def train_regressor(
        self, 
        X_train: Union[np.ndarray, pd.DataFrame], 
        y_train: Union[np.ndarray, pd.Series],
        model_type: str = "random_forest",
        model_params: Dict[str, Any] = None,
        model_name: str = None,
        save_model: bool = True,
        preprocess: bool = True,
        text_features: List[str] = None
    ) -> Dict[str, Any]:
        """
        Train a regression model
        
        Args:
            X_train: Training features
            y_train: Training labels
            model_type: Type of model to train
            model_params: Parameters for the model
            model_name: Name to save the model as
            save_model: Whether to save the model
            preprocess: Whether to preprocess the data
            text_features: List of column names containing text data
            
        Returns:
            Dictionary with training results
        """
        try:
            # Convert to DataFrame if numpy array
            if isinstance(X_train, np.ndarray):
                X_train = pd.DataFrame(X_train)
            
            # Default model parameters
            if model_params is None:
                model_params = {}
            
            # Generate model name if not provided
            if model_name is None:
                model_name = f"regressor_{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Preprocess data if requested
            preprocessors = {}
            if preprocess:
                X_train, preprocessors = self._preprocess_data(X_train, text_features)
                
                # Save preprocessors
                for name, processor in preprocessors.items():
                    processor_type = name.split("_")[0]  # e.g., "scaler", "vectorizer"
                    self.save_model(processor, f"{model_name}_{name}", processor_type)
            
            # Create model based on type
            if model_type == "random_forest":
                model = RandomForestRegressor(**model_params)
            elif model_type == "linear_regression":
                model = LinearRegression(**model_params)
            elif model_type == "svr":
                model = SVR(**model_params)
            elif model_type == "knn":
                model = KNeighborsRegressor(**model_params)
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
            
            # Train model
            model.fit(X_train, y_train)
            
            # Evaluate model
            train_predictions = model.predict(X_train)
            train_mse = mean_squared_error(y_train, train_predictions)
            train_r2 = r2_score(y_train, train_predictions)
            
            # Save model if requested
            if save_model:
                metadata = {
                    "model_type": model_type,
                    "model_params": model_params,
                    "train_mse": train_mse,
                    "train_r2": train_r2,
                    "preprocessors": list(preprocessors.keys()),
                    "created_at": datetime.now().isoformat(),
                    "feature_names": X_train.columns.tolist() if hasattr(X_train, "columns") else None,
                    "n_features": X_train.shape[1],
                    "n_samples": X_train.shape[0]
                }
                
                self.save_model(model, model_name, "model", metadata)
            
            # Return results
            return {
                "model": model,
                "model_name": model_name,
                "train_mse": train_mse,
                "train_r2": train_r2,
                "preprocessors": preprocessors
            }
            
        except Exception as e:
            logger.error(f"Error training regressor: {str(e)}")
            return {"error": str(e)}
    
    def train_anomaly_detector(
        self, 
        X_train: Union[np.ndarray, pd.DataFrame],
        model_type: str = "isolation_forest",
        model_params: Dict[str, Any] = None,
        model_name: str = None,
        save_model: bool = True,
        preprocess: bool = True,
        text_features: List[str] = None
    ) -> Dict[str, Any]:
        """
        Train an anomaly detection model
        
        Args:
            X_train: Training features
            model_type: Type of model to train
            model_params: Parameters for the model
            model_name: Name to save the model as
            save_model: Whether to save the model
            preprocess: Whether to preprocess the data
            text_features: List of column names containing text data
            
        Returns:
            Dictionary with training results
        """
        try:
            # Convert to DataFrame if numpy array
            if isinstance(X_train, np.ndarray):
                X_train = pd.DataFrame(X_train)
            
            # Default model parameters
            if model_params is None:
                model_params = {}
            
            # Generate model name if not provided
            if model_name is None:
                model_name = f"anomaly_{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Preprocess data if requested
            preprocessors = {}
            if preprocess:
                X_train, preprocessors = self._preprocess_data(X_train, text_features)
                
                # Save preprocessors
                for name, processor in preprocessors.items():
                    processor_type = name.split("_")[0]  # e.g., "scaler", "vectorizer"
                    self.save_model(processor, f"{model_name}_{name}", processor_type)
            
            # Create model based on type
            if model_type == "isolation_forest":
                model = IsolationForest(**model_params)
            elif model_type == "dbscan":
                model = DBSCAN(**model_params)
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
            
            # Train model
            model.fit(X_train)
            
            # Save model if requested
            if save_model:
                metadata = {
                    "model_type": model_type,
                    "model_params": model_params,
                    "preprocessors": list(preprocessors.keys()),
                    "created_at": datetime.now().isoformat(),
                    "feature_names": X_train.columns.tolist() if hasattr(X_train, "columns") else None,
                    "n_features": X_train.shape[1],
                    "n_samples": X_train.shape[0]
                }
                
                self.save_model(model, model_name, "model", metadata)
            
            # Return results
            return {
                "model": model,
                "model_name": model_name,
                "preprocessors": preprocessors
            }
            
        except Exception as e:
            logger.error(f"Error training anomaly detector: {str(e)}")
            return {"error": str(e)}
    
    def predict(
        self, 
        X: Union[np.ndarray, pd.DataFrame, Dict[str, Any]], 
        model_name: str,
        preprocess: bool = True
    ) -> Dict[str, Any]:
        """
        Make predictions using a trained model
        
        Args:
            X: Features to predict on
            model_name: Name of the model to use
            preprocess: Whether to preprocess the data
            
        Returns:
            Dictionary with prediction results
        """
        try:
            # Check if model exists
            if model_name not in self.models:
                return {"error": f"Model '{model_name}' not found"}
            
            model = self.models[model_name]
            
            # Convert dict to DataFrame if needed
            if isinstance(X, dict):
                X = pd.DataFrame([X])
            
            # Convert numpy array to DataFrame if needed
            if isinstance(X, np.ndarray):
                X = pd.DataFrame(X)
            
            # Preprocess data if requested
            if preprocess:
                X = self._preprocess_prediction_data(X, model_name)
            
            # Make prediction
            if hasattr(model, "predict_proba"):
                try:
                    # Try to get probability predictions
                    y_prob = model.predict_proba(X)
                    y_pred = model.predict(X)
                    
                    # Format results
                    results = []
                    for i in range(len(X)):
                        result = {
                            "prediction": y_pred[i],
                            "probabilities": {j: float(prob) for j, prob in enumerate(y_prob[i])}
                        }
                        results.append(result)
                    
                    return {"predictions": results}
                    
                except:
                    # Fall back to regular predictions
                    y_pred = model.predict(X)
                    return {"predictions": [{"prediction": pred} for pred in y_pred]}
            else:
                # Regular predictions
                y_pred = model.predict(X)
                return {"predictions": [{"prediction": pred} for pred in y_pred]}
            
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            return {"error": str(e)}
    
    def detect_anomalies(
        self, 
        X: Union[np.ndarray, pd.DataFrame, Dict[str, Any]], 
        model_name: str,
        preprocess: bool = True,
        threshold: float = None
    ) -> Dict[str, Any]:
        """
        Detect anomalies using a trained anomaly detection model
        
        Args:
            X: Features to detect anomalies in
            model_name: Name of the model to use
            preprocess: Whether to preprocess the data
            threshold: Anomaly score threshold (for models that support it)
            
        Returns:
            Dictionary with anomaly detection results
        """
        try:
            # Check if model exists
            if model_name not in self.models:
                return {"error": f"Model '{model_name}' not found"}
            
            model = self.models[model_name]
            
            # Convert dict to DataFrame if needed
            if isinstance(X, dict):
                X = pd.DataFrame([X])
            
            # Convert numpy array to DataFrame if needed
            if isinstance(X, np.ndarray):
                X = pd.DataFrame(X)
            
            # Preprocess data if requested
            if preprocess:
                X = self._preprocess_prediction_data(X, model_name)
            
            # Detect anomalies
            if hasattr(model, "decision_function"):
                # For models like IsolationForest that have decision_function
                anomaly_scores = model.decision_function(X)
                predictions = model.predict(X)
                
                # Convert predictions (-1 for anomalies, 1 for normal) to boolean
                is_anomaly = [pred == -1 for pred in predictions]
                
                # Format results
                results = []
                for i in range(len(X)):
                    result = {
                        "is_anomaly": is_anomaly[i],
                        "anomaly_score": float(anomaly_scores[i])
                    }
                    results.append(result)
                
                return {"anomalies": results}
                
            elif hasattr(model, "fit_predict"):
                # For models like DBSCAN
                predictions = model.fit_predict(X)
                
                # In DBSCAN, -1 indicates outliers
                is_anomaly = [pred == -1 for pred in predictions]
                
                # Format results
                results = []
                for i in range(len(X)):
                    result = {
                        "is_anomaly": is_anomaly[i],
                        "cluster": int(predictions[i])
                    }
                    results.append(result)
                
                return {"anomalies": results}
                
            else:
                return {"error": "Model does not support anomaly detection"}
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return {"error": str(e)}
    
    def _preprocess_data(
        self, 
        X: pd.DataFrame, 
        text_features: List[str] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Preprocess data for training
        
        Args:
            X: Features to preprocess
            text_features: List of column names containing text data
            
        Returns:
            Tuple of (preprocessed data, preprocessor objects)
        """
        preprocessors = {}
        X_processed = X.copy()
        
        try:
            # Handle text features
            if text_features:
                for text_col in text_features:
                    if text_col in X.columns:
                        # Create TF-IDF vectorizer
                        vectorizer = TfidfVectorizer(max_features=100)
                        
                        # Transform text column
                        text_features_sparse = vectorizer.fit_transform(X[text_col].fillna(""))
                        
                        # Convert to dense array and create DataFrame
                        text_features_df = pd.DataFrame(
                            text_features_sparse.toarray(),
                            columns=[f"{text_col}_tfidf_{i}" for i in range(text_features_sparse.shape[1])]
                        )
                        
                        # Add to processed data
                        X_processed = pd.concat([X_processed.drop(columns=[text_col]), text_features_df], axis=1)
                        
                        # Save vectorizer
                        preprocessors[f"vectorizer_{text_col}"] = vectorizer
            
            # Scale numerical features
            num_cols = X_processed.select_dtypes(include=np.number).columns
            if not num_cols.empty:
                scaler = StandardScaler()
                X_processed[num_cols] = scaler.fit_transform(X_processed[num_cols])
                preprocessors["scaler_numerical"] = scaler
            
            # Encode categorical features
            cat_cols = X_processed.select_dtypes(include=["object", "category"]).columns
            for col in cat_cols:
                encoder = LabelEncoder()
                X_processed[col] = encoder.fit_transform(X_processed[col].fillna("unknown"))
                preprocessors[f"encoder_{col}"] = encoder
            
            return X_processed, preprocessors
            
        except Exception as e:
            logger.error(f"Error preprocessing data: {str(e)}")
            return X, {}
    
    def _preprocess_prediction_data(self, X: pd.DataFrame, model_name: str) -> pd.DataFrame:
        """
        Preprocess data for prediction using saved preprocessors
        
        Args:
            X: Features to preprocess
            model_name: Name of the model (to find associated preprocessors)
            
        Returns:
            Preprocessed data
        """
        X_processed = X.copy()
        
        try:
            # Apply vectorizers
            for vec_name, vectorizer in self.vectorizers.items():
                if vec_name.startswith(f"{model_name}_vectorizer_"):
                    # Extract column name from vectorizer name
                    col_name = vec_name.replace(f"{model_name}_vectorizer_", "")
                    
                    if col_name in X.columns:
                        # Transform text column
                        text_features_sparse = vectorizer.transform(X[col_name].fillna(""))
                        
                        # Convert to dense array and create DataFrame
                        text_features_df = pd.DataFrame(
                            text_features_sparse.toarray(),
                            columns=[f"{col_name}_tfidf_{i}" for i in range(text_features_sparse.shape[1])]
                        )
                        
                        # Add to processed data
                        X_processed = pd.concat([X_processed.drop(columns=[col_name]), text_features_df], axis=1)
            
            # Apply scalers
            for scaler_name, scaler in self.scalers.items():
                if scaler_name.startswith(f"{model_name}_scaler_"):
                    # For numerical scaler
                    if scaler_name == f"{model_name}_scaler_numerical":
                        num_cols = X_processed.select_dtypes(include=np.number).columns
                        if not num_cols.empty:
                            X_processed[num_cols] = scaler.transform(X_processed[num_cols])
            
            # Apply encoders
            for encoder_name, encoder in self.encoders.items():
                if encoder_name.startswith(f"{model_name}_encoder_"):
                    # Extract column name from encoder name
                    col_name = encoder_name.replace(f"{model_name}_encoder_", "")
                    
                    if col_name in X.columns:
                        # Transform categorical column
                        X_processed[col_name] = encoder.transform(X_processed[col_name].fillna("unknown"))
            
            return X_processed
            
        except Exception as e:
            logger.error(f"Error preprocessing prediction data: {str(e)}")
            return X

# Create a global instance
ml_processor = MLProcessor()

def get_ml_processor() -> MLProcessor:
    """Get the global ML processor instance"""
    return ml_processor
