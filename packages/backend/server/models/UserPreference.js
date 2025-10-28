import mongoose from 'mongoose';

const userPreferenceSchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    unique: true
  },
  communicationStyle: {
    type: String,
    enum: ['casual', 'formal', 'empathetic', 'concise', 'humorous'],
    default: 'empathetic'
  },
  topics: [{
    name: String,
    interest: {
      type: Number,
      min: 1,
      max: 10,
      default: 5
    }
  }],
  memorizedDetails: [{
    key: String,
    value: String,
    timestamp: {
      type: Date,
      default: Date.now
    }
  }],
  emotionalState: {
    type: String,
    enum: ['happy', 'sad', 'neutral', 'excited', 'anxious', 'unknown'],
    default: 'unknown'
  },
  lastInteraction: {
    type: Date,
    default: Date.now
  }
});

const UserPreference = mongoose.model('UserPreference', userPreferenceSchema);

export default UserPreference;
