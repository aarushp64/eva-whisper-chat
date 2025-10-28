import User from '../models/User.js';
import UserPreference from '../models/UserPreference.js';
import axios from 'axios';

// Get user profile
export const getUserProfile = async (req, res) => {
  try {
    const user = await User.findById(req.user.id).select('-password');
    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }
    
    // Get user preferences
    const preferences = await UserPreference.findOne({ userId: req.user.id });
    
    res.json({
      user,
      preferences
    });
  } catch (error) {
    console.error('Get user profile error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// Update user profile
export const updateUserProfile = async (req, res) => {
  try {
    const { username, email } = req.body;
    
    // Check if email is already in use by another user
    if (email) {
      const existingUser = await User.findOne({ email, _id: { $ne: req.user.id } });
      if (existingUser) {
        return res.status(400).json({ message: 'Email already in use' });
      }
    }
    
    // Check if username is already in use by another user
    if (username) {
      const existingUser = await User.findOne({ username, _id: { $ne: req.user.id } });
      if (existingUser) {
        return res.status(400).json({ message: 'Username already in use' });
      }
    }
    
    // Update user
    const updatedUser = await User.findByIdAndUpdate(
      req.user.id,
      { $set: req.body },
      { new: true }
    ).select('-password');
    
    if (!updatedUser) {
      return res.status(404).json({ message: 'User not found' });
    }
    
    res.json(updatedUser);
  } catch (error) {
    console.error('Update user profile error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// Update user preferences
export const updateUserPreferences = async (req, res) => {
  try {
    const { communicationStyle, topics, emotionalState, conversation_history } = req.body;
    
    // Find or create user preferences
    let preferences = await UserPreference.findOne({ userId: req.user.id });
    
    if (!preferences) {
      preferences = new UserPreference({
        userId: req.user.id
      });
    }
    
    // Update fields if provided
    if (communicationStyle) preferences.communicationStyle = communicationStyle;
    if (emotionalState) preferences.emotionalState = emotionalState;
    
    // Update topics if provided
    if (topics && Array.isArray(topics)) {
      // For each topic in the request
      topics.forEach(newTopic => {
        // Check if the topic already exists
        const existingTopicIndex = preferences.topics.findIndex(
          t => t.name === newTopic.name
        );
        
        if (existingTopicIndex !== -1) {
          // Update existing topic
          preferences.topics[existingTopicIndex].interest = newTopic.interest;
        } else {
          // Add new topic
          preferences.topics.push(newTopic);
        }
      });
    }

    if (conversation_history) {
      try {
        const response = await axios.post('http://localhost:5000/api/user/preferences/analyze', {
          conversation_history
        }, {
          headers: {
            'Authorization': req.headers.authorization
          }
        });
        preferences.preferred_communication_style = response.data.preferred_communication_style;
        preferences.typical_sentiment = response.data.typical_sentiment;
        preferences.frequent_topics = response.data.frequent_topics;
      } catch (error) {
        console.error('Error analyzing conversation history:', error);
      }
    }
    
    // Update last interaction time
    preferences.lastInteraction = Date.now();
    
    await preferences.save();
    
    res.json(preferences);
  } catch (error) {
    console.error('Update user preferences error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// Add memorized detail for user
export const addMemorizedDetail = async (req, res) => {
  try {
    const { key, value } = req.body;
    
    if (!key || !value) {
      return res.status(400).json({ message: 'Key and value are required' });
    }
    
    // Find user preferences
    let preferences = await UserPreference.findOne({ userId: req.user.id });
    
    if (!preferences) {
      preferences = new UserPreference({
        userId: req.user.id
      });
    }
    
    // Check if the key already exists
    const existingDetailIndex = preferences.memorizedDetails.findIndex(
      detail => detail.key === key
    );
    
    if (existingDetailIndex !== -1) {
      // Update existing detail
      preferences.memorizedDetails[existingDetailIndex].value = value;
      preferences.memorizedDetails[existingDetailIndex].timestamp = Date.now();
    } else {
      // Add new detail
      preferences.memorizedDetails.push({
        key,
        value,
        timestamp: Date.now()
      });
    }
    
    await preferences.save();
    
    res.json(preferences.memorizedDetails);
  } catch (error) {
    console.error('Add memorized detail error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// Get all memorized details for user
export const getMemorizedDetails = async (req, res) => {
  try {
    const preferences = await UserPreference.findOne({ userId: req.user.id });
    
    if (!preferences) {
      return res.json([]);
    }
    
    res.json(preferences.memorizedDetails);
  } catch (error) {
    console.error('Get memorized details error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};
