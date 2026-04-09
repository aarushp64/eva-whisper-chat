import Message from '../models/Message.js';
import Chat from '../models/Chat.js';
import UserPreference from '../models/UserPreference.js';
import { analyzeUserSentiment } from '../utils/sentimentAnalysis.js';
import { generateResponse } from '../utils/responseGenerator.js';
import { updateUserEmotionalState } from '../utils/userProfiling.js';
import { extractKeyInformation } from '../utils/memoryManager.js';

// Handle incoming message and generate response
export const handleMessage = async (data) => {
  try {
    const { chatId, groupId, content, senderId, llmConfig } = data;
    
    // Determine if it's a group chat or private chat
    const isGroupChat = !!groupId;
    const messageChatId = isGroupChat ? null : chatId; // If group chat, chatId is null for Message model
    const messageGroupId = isGroupChat ? groupId : null;

    // Analyze user sentiment
    const sentiment = await analyzeUserSentiment(content);
    
    // Save user message
    const userMessage = new Message({
      chatId: messageChatId,
      groupId: messageGroupId,
      sender: senderId, // Use senderId for the actual user
      content,
      sentiment,
      chatType: isGroupChat ? 'group' : 'private'
    });
    await userMessage.save();
    
    // Update chat's last message and timestamp
    if (isGroupChat) {
      // For group chats, you might want to update the associated Chat entry (if one exists per group)
      // or a dedicated Group model's last message field.
      // Assuming Chat model is used for both private and group conversations, linked by groupId
      await Chat.findOneAndUpdate({ groupId: groupId }, {
        lastMessage: content,
        updatedAt: Date.now()
      });
    } else {
      await Chat.findByIdAndUpdate(chatId, {
        lastMessage: content,
        updatedAt: Date.now()
      });
    }
    
    // Update user emotional state based on message content
    await updateUserEmotionalState(senderId, sentiment, content);
    
    // Extract and store any key information from the message
    await extractKeyInformation(senderId, content);

    // Get user preferences to personalize response
    const userPreference = await UserPreference.findOne({ userId: senderId });

    // Generate EVA's response (pass runtime LLM config if provided)
    const responseContent = await generateResponse(content, userPreference, sentiment, isGroupChat, llmConfig);
    
    // Save EVA's response
    const assistantMessage = new Message({
      chatId: messageChatId,
      groupId: messageGroupId,
      sender: 'assistant',
      content: responseContent,
      sentiment: 'neutral', // EVA's responses are generally neutral in sentiment analysis
      chatType: isGroupChat ? 'group' : 'private'
    });
    await assistantMessage.save();
    
    // Update chat's last message again
    if (isGroupChat) {
      await Chat.findOneAndUpdate({ groupId: groupId }, {
        lastMessage: responseContent,
        updatedAt: Date.now()
      });
    } else {
      await Chat.findByIdAndUpdate(chatId, {
        lastMessage: responseContent,
        updatedAt: Date.now()
      });
    }
    
    return {
      message: assistantMessage,
      userMessage
    };
  } catch (error) {
    console.error('Handle message error:', error);
    throw error;
  }
};

// Add message to chat (API endpoint version)
export const addMessage = async (req, res) => {
  try {
    const { chatId, content } = req.body;
    
    // Verify the chat belongs to the user
    const chat = await Chat.findOne({ 
      _id: chatId,
      userId: req.user.id
    });
    
    if (!chat) {
      return res.status(404).json({ message: 'Chat not found' });
    }
    
    // Process the message using the handleMessage function
    const result = await handleMessage({
      chatId,
      content,
      userId: req.user.id
    });
    
    res.status(201).json(result);
  } catch (error) {
    console.error('Add message error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// Get a single message by ID
export const getMessageById = async (req, res) => {
  try {
    const message = await Message.findById(req.params.id);
    
    if (!message) {
      return res.status(404).json({ message: 'Message not found' });
    }
    
    // Verify the message belongs to a chat owned by the user
    const chat = await Chat.findOne({
      _id: message.chatId,
      userId: req.user.id
    });
    
    if (!chat) {
      return res.status(403).json({ message: 'Not authorized to access this message' });
    }
    
    res.json(message);
  } catch (error) {
    console.error('Get message by ID error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// Delete a message
export const deleteMessage = async (req, res) => {
  try {
    const message = await Message.findById(req.params.id);
    
    if (!message) {
      return res.status(404).json({ message: 'Message not found' });
    }
    
    // Verify the message belongs to a chat owned by the user
    const chat = await Chat.findOne({
      _id: message.chatId,
      userId: req.user.id
    });
    
    if (!chat) {
      return res.status(403).json({ message: 'Not authorized to delete this message' });
    }
    
    await Message.findByIdAndDelete(req.params.id);
    
    res.json({ message: 'Message deleted successfully' });
  } catch (error) {
    console.error('Delete message error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};
