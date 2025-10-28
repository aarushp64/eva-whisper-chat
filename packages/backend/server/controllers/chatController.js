import Chat from '../models/Chat.js';
import Message from '../models/Message.js';
import UserPreference from '../models/UserPreference.js';

// Get all chats for a user
export const getChats = async (req, res) => {
  try {
    const chats = await Chat.find({ userId: req.user.id })
      .sort({ updatedAt: -1 });
    
    res.json(chats);
  } catch (error) {
    console.error('Get chats error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// Create a new chat
export const createChat = async (req, res) => {
  try {
    const { title } = req.body;
    
    const newChat = new Chat({
      userId: req.user.id,
      title: title || 'New Conversation',
    });
    
    await newChat.save();
    
    // Add initial greeting message from EVA
    const welcomeMessage = new Message({
      chatId: newChat._id,
      sender: 'assistant',
      content: "Hi, I'm EVA! How can I assist you today?",
      sentiment: 'positive'
    });
    
    await welcomeMessage.save();
    
    // Update the chat with the last message
    newChat.lastMessage = welcomeMessage.content;
    await newChat.save();
    
    res.status(201).json(newChat);
  } catch (error) {
    console.error('Create chat error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// Get a single chat by ID
export const getChatById = async (req, res) => {
  try {
    const chat = await Chat.findOne({ 
      _id: req.params.id,
      userId: req.user.id
    });
    
    if (!chat) {
      return res.status(404).json({ message: 'Chat not found' });
    }
    
    res.json(chat);
  } catch (error) {
    console.error('Get chat by ID error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// Update chat title
export const updateChat = async (req, res) => {
  try {
    const { title } = req.body;
    
    const chat = await Chat.findOneAndUpdate(
      { _id: req.params.id, userId: req.user.id },
      { title, updatedAt: Date.now() },
      { new: true }
    );
    
    if (!chat) {
      return res.status(404).json({ message: 'Chat not found' });
    }
    
    res.json(chat);
  } catch (error) {
    console.error('Update chat error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// Delete a chat
export const deleteChat = async (req, res) => {
  try {
    const chat = await Chat.findOneAndDelete({ 
      _id: req.params.id,
      userId: req.user.id
    });
    
    if (!chat) {
      return res.status(404).json({ message: 'Chat not found' });
    }
    
    // Delete all messages in the chat
    await Message.deleteMany({ chatId: req.params.id });
    
    res.json({ message: 'Chat deleted successfully' });
  } catch (error) {
    console.error('Delete chat error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// Get all messages for a chat
export const getChatMessages = async (req, res) => {
  try {
    // First verify the chat belongs to the user
    const chat = await Chat.findOne({ 
      _id: req.params.id,
      userId: req.user.id
    });
    
    if (!chat) {
      return res.status(404).json({ message: 'Chat not found' });
    }
    
    const messages = await Message.find({ chatId: req.params.id })
      .sort({ timestamp: 1 });
    
    res.json(messages);
  } catch (error) {
    console.error('Get chat messages error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};
