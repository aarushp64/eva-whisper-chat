import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import morgan from 'morgan';
import { Server } from 'socket.io';
import http from 'http';
import mongoose from 'mongoose';

// Import routes
import authRoutes from './routes/auth.js';
import chatRoutes from './routes/chat.js';
import userRoutes from './routes/user.js';
import groupRoutes from './routes/group.js';

// Import controllers
import { handleMessage } from './controllers/messageController.js';
import { SpeechProcessor } from './speech/speech_processor.js';
import { streamTTS } from './src/ai/tts/engine.js';

const speechProcessor = new SpeechProcessor();

// Load environment variables
dotenv.config();

// Initialize Express app
const app = express();
const server = http.createServer(app);

// Set up Socket.io
const io = new Server(server, {
  cors: {
    origin: process.env.CLIENT_URL || 'http://localhost:5173',
    methods: ['GET', 'POST']
  }
});

// Middleware
app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

// Database connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/eva-assistant')
  .then(() => console.log('Connected to MongoDB'))
  .catch(err => console.error('MongoDB connection error:', err));

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/chat', chatRoutes);
app.use('/api/user', userRoutes);
app.use('/api/group', groupRoutes);

// Socket.io connection
import jwt from 'jsonwebtoken';
import GroupMember from './models/GroupMember.js';

io.on('connection', (socket) => {
  console.log('User connected:', socket.id);

  // Authenticate socket connection (optional, but good practice)
  socket.on('authenticate', (token) => {
    try {
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      socket.userId = decoded.id; // Attach user ID to socket
      console.log(`User ${socket.userId} authenticated via socket.`);
    } catch (error) {
      console.log('Socket authentication failed:', error.message);
      socket.disconnect(true); // Disconnect unauthenticated socket
    }
  });

  socket.on('join_chat', (chatId) => {
    socket.join(chatId);
    console.log(`User ${socket.id} joined private chat ${chatId}`);
  });

  socket.on('leave_chat', (chatId) => {
    socket.leave(chatId);
    console.log(`User ${socket.id} left private chat ${chatId}`);
  });

  socket.on('join_group_chat', async (groupId) => {
    if (!socket.userId) {
      socket.emit('error', { message: 'Authentication required to join group chat' });
      return;
    }
    // Verify user is a member of the group
    const isMember = await GroupMember.findOne({ groupId, userId: socket.userId });
    if (isMember) {
      socket.join(groupId);
      console.log(`User ${socket.userId} joined group chat ${groupId}`);
    } else {
      socket.emit('error', { message: 'Not authorized to join this group chat' });
    }
  });

  socket.on('leave_group_chat', (groupId) => {
    socket.leave(groupId);
    console.log(`User ${socket.userId} left group chat ${groupId}`);
  });

  socket.on('typing', ({ chatId, isTyping }) => {
    socket.to(chatId).emit('typing', { isTyping });
  });
  
  socket.on('send_message', async (data) => {
    try {
      // Basic validation: ensure sender is authenticated
      if (!socket.userId) {
        socket.emit('error', { message: 'Authentication required to send message' });
        return;
      }

      // Determine if it's a private chat or group chat
      const isGroupChat = data.groupId; // Assuming groupId is present for group chats
      const targetRoom = isGroupChat ? data.groupId : data.chatId;

      // For group chats, verify user is a member
      if (isGroupChat) {
        const isMember = await GroupMember.findOne({ groupId: data.groupId, userId: socket.userId });
        if (!isMember) {
          socket.emit('error', { message: 'Not authorized to send messages to this group' });
          return;
        }
      }

      // Pass senderId, LLM config, and optional approval result to handleMessage.
      // llmConfig: { provider, model, apiKey, approvalResult }
      // approvalResult: { sessionId, approved } — for HITL resume
      const messageData = { ...data, senderId: socket.userId };
      const response = await handleMessage(messageData);

      // Detect HITL approval response and emit a dedicated event
      if (response?.message?.isApproval) {
        io.to(targetRoom).emit('approval_request', {
          content: response.message.content,
          pendingApproval: response.message.pendingApproval,
          sessionId: response.message.sessionId,
        });
      } else {
        io.to(targetRoom).emit('receive_message', response);
      }
    } catch (error) {
      console.error('Error processing message:', error);
      socket.emit('error', { message: 'Error processing your message' });
    }
  });

  socket.on("voice_message", async ({ audioBlob, llmConfig }) => {
    try {
      const audioBase64 = audioBlob.toString("base64");
      const { transcription, error } = await speechProcessor.transcribe_audio_base64(
        audioBase64,
        "webm"
      );

      if (error) {
        console.warn("[Voice] Whisper failed:", error);
        socket.emit("receive_message", { role: "assistant", message: { content: "Sorry, I couldn't hear you.", role: "assistant" } });
        return;
      }

      const { detectIntent } = await import("./src/ai/intent.js");
      const intentInfo = detectIntent(transcription, { structured: true });

      const messageData = {
        chatId: null,
        text: transcription,
        senderId: socket.userId || 'anonymous_user',
        llmConfig,
        intent: intentInfo.intent,
        confidence: intentInfo.confidence,
      };

      const response = await handleMessage(messageData);
      const targetRoom = messageData.groupId ? messageData.groupId : messageData.chatId;
      
      if (response?.message?.isApproval) {
        io.to(targetRoom || socket.id).emit('approval_request', {
          content: response.message.content,
          pendingApproval: response.message.pendingApproval,
          sessionId: response.message.sessionId,
        });
      } else {
        io.to(targetRoom || socket.id).emit("chat_message", { message: response.message.content || response.text, user: 'eva' });
      }

      if (llmConfig?.enableTTS && (response?.message?.content || response?.text)) {
        const text = response.message?.content || response.text;
        const ttsProvider = process.env.TTS_PROVIDER || "edge";

        for await (const chunk of streamTTS(text, { provider: ttsProvider })) {
          const audioBase64 = Buffer.from(chunk).toString("base64");
          io.to(socket.id).emit("tts_chunk", { audioBase64 });
        }
      }
    } catch (err) {
      console.error("[Voice] processing error:", err);
      socket.emit("chat_message", { user: 'eva', message: "I ran into an error while processing your voice request." });
    }
  });

  socket.on('typing', ({ room, user }) => {
    socket.to(room).emit('user_typing', { user });
  });

  socket.on('stop_typing', ({ room, user }) => {
    socket.to(room).emit('user_stopped_typing', { user });
  });

  socket.on('disconnect', () => {
    console.log('User disconnected:', socket.id);
  });
});

// Default route
app.get('/', (req, res) => {
  res.send('EVA Assistant API is running');
});

// Start server
const PORT = process.env.PORT || 8080;

export { app, server };
server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
