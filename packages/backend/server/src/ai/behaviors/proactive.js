import { storeMemory } from '../memory/semantic.js';

export async function generateDailyBriefing(semanticMemories, calendarData) {
  const events = calendarData?.data?.length || 0;
  return `[System Briefing] Today you have ${events} meetings. Based on your memory, remember: ${
    semanticMemories[0]?.content || "No immediate concerns."
  }`;
}

export function checkProactiveSuggestions(intentHistory) {
  const recentIntents = intentHistory.slice(-3);
  if (recentIntents.every(i => i.intent === 'COMMUNICATION')) {
    return "You've been messaging a lot today. Shall I draft a summary email to the team?";
  }
  return null;
}

export async function capturePreferences(sessionId, rawInput) {
  if (rawInput.toLowerCase().includes('remember i prefer') || rawInput.toLowerCase().includes('keep in mind')) {
    const preference = rawInput.replace(/remember i prefer/i, '').replace(/keep in mind/i, '').trim();
    await storeMemory(sessionId, preference, { intent: 'PREFERENCE_CAPTURE', category: 'user_prefs' });
    return true;
  }
  return false;
}
