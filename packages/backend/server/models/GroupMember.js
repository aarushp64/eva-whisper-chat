import mongoose from 'mongoose';

const groupMemberSchema = new mongoose.Schema({
  groupId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Group',
    required: true,
  },
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
  },
  joinedAt: {
    type: Date,
    default: Date.now,
  },
});

// Ensure unique combination of groupId and userId
groupMemberSchema.index({ groupId: 1, userId: 1 }, { unique: true });

const GroupMember = mongoose.model('GroupMember', groupMemberSchema);

export default GroupMember;
