import express from 'express';
import { createGroup, inviteUserToGroup, getUserGroups, getGroupMembers } from '../controllers/groupController.js';
import { auth } from '../middleware/auth.js';

const router = express.Router();

// @route   POST /api/group
// @desc    Create a new group
// @access  Private
router.post('/', auth, createGroup);

// @route   POST /api/group/invite
// @desc    Invite user to a group
// @access  Private
router.post('/invite', auth, inviteUserToGroup);

// @route   GET /api/group/my-groups
// @desc    Get groups a user is a member of
// @access  Private
router.get('/my-groups', auth, getUserGroups);

// @route   GET /api/group/:groupId/members
// @desc    Get members of a specific group
// @access  Private
router.get('/:groupId/members', auth, getGroupMembers);

export default router;
