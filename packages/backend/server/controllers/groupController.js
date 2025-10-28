import Group from '../models/Group.js';
import GroupMember from '../models/GroupMember.js';
import User from '../models/User.js';

// Create a new group
export const createGroup = async (req, res) => {
  try {
    const { name, description } = req.body;
    const createdBy = req.user.id; // Assuming user ID is available from JWT

    // Check if group name already exists
    const existingGroup = await Group.findOne({ name });
    if (existingGroup) {
      return res.status(400).json({ message: 'Group with this name already exists' });
    }

    const newGroup = new Group({
      name,
      description,
      createdBy,
    });

    await newGroup.save();

    // Add creator as a member
    const creatorMember = new GroupMember({
      groupId: newGroup._id,
      userId: createdBy,
    });
    await creatorMember.save();

    res.status(201).json(newGroup);
  } catch (error) {
    console.error('Create group error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// Invite user to a group
export const inviteUserToGroup = async (req, res) => {
  try {
    const { groupId, userId } = req.body;
    const invitingUser = req.user.id; // User performing the invite

    // Check if inviting user is a member of the group (optional: check if admin/creator)
    const isInvitingUserMember = await GroupMember.findOne({ groupId, userId: invitingUser });
    if (!isInvitingUserMember) {
      return res.status(403).json({ message: 'You are not authorized to invite users to this group' });
    }

    // Check if invited user exists
    const invitedUser = await User.findById(userId);
    if (!invitedUser) {
      return res.status(404).json({ message: 'Invited user not found' });
    }

    // Check if user is already a member
    const alreadyMember = await GroupMember.findOne({ groupId, userId });
    if (alreadyMember) {
      return res.status(400).json({ message: 'User is already a member of this group' });
    }

    const newMember = new GroupMember({
      groupId,
      userId,
    });
    await newMember.save();

    res.status(200).json({ message: 'User invited to group successfully' });
  } catch (error) {
    console.error('Invite user to group error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// Get groups a user is a member of
export const getUserGroups = async (req, res) => {
  try {
    const userId = req.user.id;
    const memberEntries = await GroupMember.find({ userId }).populate('groupId');
    const groups = memberEntries.map(entry => entry.groupId);
    res.status(200).json(groups);
  } catch (error) {
    console.error('Get user groups error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// Get members of a specific group
export const getGroupMembers = async (req, res) => {
  try {
    const groupId = req.params.groupId;
    const userId = req.user.id; // User requesting the members

    // Check if the requesting user is a member of the group
    const isMember = await GroupMember.findOne({ groupId, userId });
    if (!isMember) {
      return res.status(403).json({ message: 'You are not a member of this group' });
    }

    const members = await GroupMember.find({ groupId }).populate('userId', 'username email');
    const memberDetails = members.map(member => member.userId);
    res.status(200).json(memberDetails);
  } catch (error) {
    console.error('Get group members error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};
