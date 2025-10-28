import express from 'express';
import { 
  getChats, 
  createChat, 
  getChatById, 
  updateChat, 
  deleteChat,
  getChatMessages
} from '../controllers/chatController.js';
import { addMessage, getMessageById, deleteMessage } from '../controllers/messageController.js';
import { auth } from '../middleware/auth.js';

const router = express.Router();

// Apply auth middleware to all routes
router.use(auth);

// Chat routes
router.get('/', getChats);
router.post('/', createChat);
router.get('/:id', getChatById);
router.put('/:id', updateChat);
router.delete('/:id', deleteChat);
router.get('/:id/messages', getChatMessages);

// Message routes
router.post('/message', addMessage);
router.get('/message/:id', getMessageById);
router.delete('/message/:id', deleteMessage);

export default router;
