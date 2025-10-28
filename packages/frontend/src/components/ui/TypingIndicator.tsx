import React from 'react';

interface TypingIndicatorProps {
  typingUsers: string[];
}

const TypingIndicator: React.FC<TypingIndicatorProps> = ({ typingUsers }) => {
  if (typingUsers.length === 0) {
    return null;
  }

  const usersText = typingUsers.length === 1
    ? `${typingUsers[0]} is typing...`
    : typingUsers.length === 2
      ? `${typingUsers.join(' and ')} are typing...`
      : `${typingUsers.slice(0, 2).join(', ')} and others are typing...`;

  return (
    <div className="text-sm text-muted-foreground italic px-4 py-2">
      {usersText}
    </div>
  );
};

export default TypingIndicator;
