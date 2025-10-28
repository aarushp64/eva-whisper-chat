import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime
import pickle

class UserPersonalizationModel:
    """Class to handle user personalization and prediction"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.message_history = []
        self.user_profile = {}
        self.topic_clusters = None
        self.response_model = None
        self.tfidf_vectorizer = None
        self.pca = None
        self.scaler = None
    
    def add_message(self, message):
        """
        Add a message to the user's history
        
        Args:
            message (dict): Message object with sender, content, timestamp, and metadata
        """
        self.message_history.append(message)
    
    def update_user_profile(self, profile_data):
        """
        Update the user's profile with new data
        
        Args:
            profile_data (dict): User profile data
        """
        self.user_profile.update(profile_data)
    
    def cluster_topics(self, n_clusters=5):
        """
        Cluster user messages into topics
        
        Args:
            n_clusters (int): Number of clusters to create
            
        Returns:
            dict: Cluster information including centroids and labels
        """
        # Extract user messages
        user_messages = [m["content"] for m in self.message_history if m["sender"] == "user"]
        
        if len(user_messages) < n_clusters:
            return None
        
        # Create TF-IDF vectorizer
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            min_df=2
        )
        
        # Transform messages to TF-IDF features
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(user_messages)
        
        # Apply dimensionality reduction if needed
        if tfidf_matrix.shape[1] > 50:
            self.pca = PCA(n_components=min(50, tfidf_matrix.shape[1]))
            features = self.pca.fit_transform(tfidf_matrix.toarray())
        else:
            features = tfidf_matrix.toarray()
        
        # Standardize features
        self.scaler = StandardScaler()
        scaled_features = self.scaler.fit_transform(features)
        
        # Apply K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(scaled_features)
        
        # Create cluster information
        self.topic_clusters = {
            "model": kmeans,
            "labels": cluster_labels,
            "centroids": kmeans.cluster_centers_,
            "messages": user_messages,
            "features": scaled_features
        }
        
        # Extract top terms for each cluster
        top_terms_per_cluster = self._get_top_terms_per_cluster(
            self.tfidf_vectorizer, kmeans, n_terms=10
        )
        
        # Create cluster summaries
        cluster_summaries = {}
        for cluster_id, terms in top_terms_per_cluster.items():
            # Get messages in this cluster
            cluster_messages = [
                user_messages[i] for i in range(len(user_messages)) 
                if cluster_labels[i] == cluster_id
            ]
            
            cluster_summaries[cluster_id] = {
                "top_terms": terms,
                "message_count": len(cluster_messages),
                "sample_messages": cluster_messages[:3]
            }
        
        return {
            "n_clusters": n_clusters,
            "cluster_summaries": cluster_summaries
        }
    
    def _get_top_terms_per_cluster(self, vectorizer, kmeans, n_terms=10):
        """Get top terms for each cluster"""
        order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
        terms = vectorizer.get_feature_names_out()
        
        top_terms = {}
        for cluster_id in range(kmeans.n_clusters):
            top_terms[cluster_id] = [
                terms[ind] for ind in order_centroids[cluster_id, :n_terms]
            ]
        
        return top_terms
    
    def analyze_conversation_history(self, conversation_history):
        """
        Analyze the user's conversation history to determine typical sentiment, 
        communication style, and frequent topics.
        
        Args:
            conversation_history (list): List of message objects
        
        Returns:
            dict: Analysis results with sentiment, style, and topics
        """
        # Extract user messages
        user_messages = [m["content"] for m in conversation_history if m["sender"] == "user"]
        
        if not user_messages:
            return {
                "sentiment": "unknown",
                "style": "unknown",
                "topics": []
            }
        
        # Analyze sentiment
        sentiment_scores = [self._get_sentiment(m) for m in user_messages]
        avg_sentiment = np.mean(sentiment_scores)
        
        if avg_sentiment > 0.2:
            typical_sentiment = "positive"
        elif avg_sentiment < -0.2:
            typical_sentiment = "negative"
        else:
            typical_sentiment = "neutral"
            
        # Analyze communication style
        communication_style = self._get_communication_style(user_messages)
        
        # Identify frequent topics
        frequent_topics = self._get_frequent_topics(user_messages)
        
        return {
            "sentiment": typical_sentiment,
            "style": communication_style,
            "topics": frequent_topics
        }

    def _get_sentiment(self, text):
        """Get sentiment score for a given text"""
        # This is a placeholder. In a real implementation, you would use an NLP library.
        # For demonstration, we'll use a simple keyword-based approach.
        positive_words = ["good", "great", "happy", "love", "like"]
        negative_words = ["bad", "sad", "hate", "dislike", "problem"]
        
        score = 0
        for word in text.lower().split():
            if word in positive_words:
                score += 1
            elif word in negative_words:
                score -= 1
        
        return score / len(text.split()) if text.split() else 0

    def _get_communication_style(self, messages):
        """Determine communication style from a list of messages"""
        # Simple heuristic based on message length and complexity
        avg_length = sum(len(m.split()) for m in messages) / len(messages)
        
        # Calculate average word length (as a simple proxy for complexity)
        all_words = [word for message in messages for word in message.split()]
        avg_word_length = sum(len(word) for word in all_words) / len(all_words) if all_words else 0
        
        # Determine style based on message characteristics
        if avg_length < 5:
            return "concise"
        elif avg_length > 20 and avg_word_length > 5:
            return "formal"
        elif avg_length > 15:
            return "detailed"
        else:
            return "casual"

    def _get_frequent_topics(self, messages, n_topics=5):
        """Identify frequent topics from a list of messages"""
        if len(messages) < n_topics:
            return []
        
        # Create TF-IDF vectorizer
        tfidf_vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            min_df=2
        )
        
        # Transform messages to TF-IDF features
        try:
            tfidf_matrix = tfidf_vectorizer.fit_transform(messages)
            
            # Get feature names
            feature_names = tfidf_vectorizer.get_feature_names_out()
            
            # Sum TF-IDF scores for each term
            summed_tfidf = tfidf_matrix.sum(axis=0)
            
            # Get top N terms
            top_indices = summed_tfidf.argsort()[0, ::-1][0, :n_topics]
            
            # Convert indices to terms
            top_topics = [feature_names[i] for i in top_indices.tolist()[0]]
            
            return top_topics
        except ValueError:
            # Not enough documents to meet min_df
            return []

    def predict_user_interests(self):
        """
        Predict user interests based on message history
        
        Returns:
            dict: Predicted user interests
        """
        if not self.topic_clusters:
            # Try to cluster topics first
            self.cluster_topics()
            
            if not self.topic_clusters:
                return {}
        
        # Get cluster with most messages
        cluster_counts = {}
        for label in self.topic_clusters["labels"]:
            if label not in cluster_counts:
                cluster_counts[label] = 0
            cluster_counts[label] += 1
        
        top_cluster = max(cluster_counts, key=cluster_counts.get)
        
        # Get top terms for the most popular cluster
        top_terms = self._get_top_terms_per_cluster(
            self.tfidf_vectorizer, self.topic_clusters["model"]
        )[top_cluster]
        
        # Create interest scores
        interests = {}
        for term in top_terms:
            interests[term] = cluster_counts[top_cluster] / len(self.topic_clusters["labels"])
        
        return interests
    
    def predict_response_style(self):
        """
        Predict the best response style for the user
        
        Returns:
            str: Predicted response style
        """
        # Simple heuristic based on message length and complexity
        user_messages = [m["content"] for m in self.message_history if m["sender"] == "user"]
        
        if not user_messages:
            return "empathetic"  # Default
        
        # Calculate average message length
        avg_length = sum(len(m.split()) for m in user_messages) / len(user_messages)
        
        # Calculate average word length (as a simple proxy for complexity)
        all_words = [word for message in user_messages for word in message.split()]
        avg_word_length = sum(len(word) for word in all_words) / len(all_words) if all_words else 0
        
        # Determine style based on message characteristics
        if avg_length < 5:
            return "concise"  # User sends short messages, respond concisely
        elif avg_length > 20 and avg_word_length > 5:
            return "formal"  # User sends long, complex messages, respond formally
        elif avg_length > 15:
            return "detailed"  # User sends longer messages, provide detail
        else:
            return "empathetic"  # Default to empathetic for medium-length messages
    
    def train_response_model(self):
        """
        Train a model to predict user satisfaction with responses
        
        Returns:
            bool: True if successful, False otherwise
        """
        # This is a placeholder for a more sophisticated model
        # In a real implementation, you would use message pairs and feedback
        
        # Check if we have enough data
        if len(self.message_history) < 10:
            return False
        
        # Extract message pairs (user message + assistant response)
        message_pairs = []
        for i in range(len(self.message_history) - 1):
            if (self.message_history[i]["sender"] == "user" and 
                self.message_history[i+1]["sender"] == "assistant"):
                
                pair = {
                    "user_message": self.message_history[i]["content"],
                    "assistant_response": self.message_history[i+1]["content"],
                    "timestamp": self.message_history[i+1]["timestamp"]
                }
                
                # Add feedback if available
                if "feedback" in self.message_history[i+1]:
                    pair["feedback"] = self.message_history[i+1]["feedback"]
                else:
                    pair["feedback"] = None
                
                message_pairs.append(pair)
        
        # If we don't have enough pairs with feedback, we can't train
        pairs_with_feedback = [p for p in message_pairs if p["feedback"] is not None]
        if len(pairs_with_feedback) < 5:
            return False
        
        # In a real implementation, you would train a model here
        # For now, we'll just store the pairs for reference
        self.response_model = {
            "message_pairs": message_pairs,
            "trained_at": datetime.now().isoformat()
        }
        
        return True
    
    def save(self, directory="models"):
        """
        Save the personalization model to disk
        
        Args:
            directory (str): Directory to save the model to
        """
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Create a filename based on user_id
        filename = f"{directory}/personalization_{self.user_id}.pkl"
        
        # Prepare data for saving
        data = {
            "user_id": self.user_id,
            "user_profile": self.user_profile,
            "message_history": self.message_history,
            "response_model": self.response_model,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save the main data
        with open(filename, "wb") as f:
            pickle.dump(data, f)
        
        # Save models if they exist
        if self.topic_clusters and "model" in self.topic_clusters:
            model_filename = f"{directory}/kmeans_{self.user_id}.pkl"
            joblib.dump(self.topic_clusters["model"], model_filename)
        
        if self.tfidf_vectorizer:
            vectorizer_filename = f"{directory}/tfidf_{self.user_id}.pkl"
            joblib.dump(self.tfidf_vectorizer, vectorizer_filename)
        
        if self.pca:
            pca_filename = f"{directory}/pca_{self.user_id}.pkl"
            joblib.dump(self.pca, pca_filename)
        
        if self.scaler:
            scaler_filename = f"{directory}/scaler_{self.user_id}.pkl"
            joblib.dump(self.scaler, scaler_filename)
    
    @classmethod
    def load(cls, user_id, directory="models"):
        """
        Load a personalization model from disk
        
        Args:
            user_id (str): User ID
            directory (str): Directory to load the model from
            
        Returns:
            UserPersonalizationModel: Loaded personalization model
        """
        # Create filename based on user_id
        filename = f"{directory}/personalization_{user_id}.pkl"
        
        # Check if file exists
        if not os.path.exists(filename):
            return cls(user_id)
        
        try:
            # Load data
            with open(filename, "rb") as f:
                data = pickle.load(f)
            
            # Create a new instance
            model = cls(user_id)
            model.user_profile = data["user_profile"]
            model.message_history = data["message_history"]
            model.response_model = data["response_model"]
            
            # Load models if they exist
            model_filename = f"{directory}/kmeans_{user_id}.pkl"
            if os.path.exists(model_filename):
                kmeans_model = joblib.load(model_filename)
                
                # Recreate topic_clusters
                model.topic_clusters = {
                    "model": kmeans_model,
                    "labels": [],  # Will be populated when clustering is done
                    "centroids": kmeans_model.cluster_centers_,
                    "messages": [],
                    "features": []
                }
            
            vectorizer_filename = f"{directory}/tfidf_{user_id}.pkl"
            if os.path.exists(vectorizer_filename):
                model.tfidf_vectorizer = joblib.load(vectorizer_filename)
            
            pca_filename = f"{directory}/pca_{user_id}.pkl"
            if os.path.exists(pca_filename):
                model.pca = joblib.load(pca_filename)
            
            scaler_filename = f"{directory}/scaler_{user_id}.pkl"
            if os.path.exists(scaler_filename):
                model.scaler = joblib.load(scaler_filename)
            
            return model
        except Exception as e:
            print(f"Error loading personalization model: {str(e)}")
            return cls(user_id)


class UserSegmentation:
    """Class to handle user segmentation and clustering"""
    
    def __init__(self):
        self.user_profiles = {}
        self.cluster_model = None
        self.feature_columns = []
    
    def add_user_profile(self, user_id, profile_data):
        """
        Add a user profile to the segmentation model
        
        Args:
            user_id (str): User ID
            profile_data (dict): User profile data
        """
        self.user_profiles[user_id] = profile_data
    
    def prepare_features(self):
        """
        Prepare features for clustering
        
        Returns:
            pandas.DataFrame: Feature dataframe
        """
        if not self.user_profiles:
            return None
        
        # Convert profiles to dataframe
        df = pd.DataFrame.from_dict(self.user_profiles, orient='index')
        
        # Handle missing values
        df = df.fillna(0)
        
        # Select numeric columns for clustering
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Store feature columns for future use
        self.feature_columns = numeric_cols
        
        return df[numeric_cols]
    
    def cluster_users(self, n_clusters=3):
        """
        Cluster users based on their profiles
        
        Args:
            n_clusters (int): Number of clusters to create
            
        Returns:
            dict: Cluster information including centroids and labels
        """
        # Prepare features
        features_df = self.prepare_features()
        
        if features_df is None or len(features_df) < n_clusters:
            return None
        
        # Standardize features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features_df)
        
        # Apply K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(scaled_features)
        
        # Create cluster information
        self.cluster_model = {
            "model": kmeans,
            "scaler": scaler,
            "labels": cluster_labels,
            "centroids": kmeans.cluster_centers_,
            "feature_columns": self.feature_columns
        }
        
        # Map user IDs to clusters
        user_clusters = {}
        for i, user_id in enumerate(self.user_profiles.keys()):
            user_clusters[user_id] = int(cluster_labels[i])
        
        # Create cluster summaries
        cluster_summaries = {}
        for cluster_id in range(n_clusters):
            # Get users in this cluster
            cluster_users = [
                user_id for user_id, label in user_clusters.items() 
                if label == cluster_id
            ]
            
            cluster_summaries[cluster_id] = {
                "user_count": len(cluster_users),
                "sample_users": cluster_users[:5]
            }
            
            # Calculate average profile for this cluster
            cluster_profiles = [
                self.user_profiles[user_id] for user_id in cluster_users
            ]
            
            if cluster_profiles:
                # Create a dataframe of cluster profiles
                cluster_df = pd.DataFrame(cluster_profiles)
                
                # Calculate mean for numeric columns
                numeric_cols = cluster_df.select_dtypes(include=[np.number]).columns.tolist()
                cluster_avg = cluster_df[numeric_cols].mean().to_dict()
                
                # Add to cluster summary
                cluster_summaries[cluster_id]["average_profile"] = cluster_avg
        
        return {
            "n_clusters": n_clusters,
            "user_clusters": user_clusters,
            "cluster_summaries": cluster_summaries
        }
    
    def predict_cluster(self, profile_data):
        """
        Predict the cluster for a new user profile
        
        Args:
            profile_data (dict): User profile data
            
        Returns:
            int: Predicted cluster ID
        """
        if self.cluster_model is None:
            return None
        
        # Convert profile to features
        features = []
        for col in self.feature_columns:
            features.append(profile_data.get(col, 0))
        
        # Convert to numpy array
        features = np.array(features).reshape(1, -1)
        
        # Standardize features
        scaled_features = self.cluster_model["scaler"].transform(features)
        
        # Predict cluster
        cluster = self.cluster_model["model"].predict(scaled_features)[0]
        
        return int(cluster)
    
    def save(self, filename="models/user_segmentation.pkl"):
        """
        Save the segmentation model to disk
        
        Args:
            filename (str): Filename to save the model to
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Prepare data for saving
        data = {
            "user_profiles": self.user_profiles,
            "feature_columns": self.feature_columns,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save the main data
        with open(filename, "wb") as f:
            pickle.dump(data, f)
        
        # Save cluster model if it exists
        if self.cluster_model:
            model_filename = filename.replace(".pkl", "_kmeans.pkl")
            joblib.dump(self.cluster_model["model"], model_filename)
            
            scaler_filename = filename.replace(".pkl", "_scaler.pkl")
            joblib.dump(self.cluster_model["scaler"], scaler_filename)
    
    @classmethod
    def load(cls, filename="models/user_segmentation.pkl"):
        """
        Load a segmentation model from disk
        
        Args:
            filename (str): Filename to load the model from
            
        Returns:
            UserSegmentation: Loaded segmentation model
        """
        # Check if file exists
        if not os.path.exists(filename):
            return cls()
        
        try:
            # Load data
            with open(filename, "rb") as f:
                data = pickle.load(f)
            
            # Create a new instance
            model = cls()
            model.user_profiles = data["user_profiles"]
            model.feature_columns = data["feature_columns"]
            
            # Load cluster model if it exists
            model_filename = filename.replace(".pkl", "_kmeans.pkl")
            scaler_filename = filename.replace(".pkl", "_scaler.pkl")
            
            if os.path.exists(model_filename) and os.path.exists(scaler_filename):
                kmeans_model = joblib.load(model_filename)
                scaler = joblib.load(scaler_filename)
                
                # Recreate cluster_model
                model.cluster_model = {
                    "model": kmeans_model,
                    "scaler": scaler,
                    "labels": [],  # Will be populated when clustering is done
                    "centroids": kmeans_model.cluster_centers_,
                    "feature_columns": model.feature_columns
                }
            
            return model
        except Exception as e:
            print(f"Error loading segmentation model: {str(e)}")
            return cls()
