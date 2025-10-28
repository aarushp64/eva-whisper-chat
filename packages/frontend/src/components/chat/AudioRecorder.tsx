import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Mic, Square, Send } from 'lucide-react';
import { toast } from 'sonner';

interface AudioRecorderProps {
  onAudioMessage: (audioData: string, format: string) => void;
  isProcessing?: boolean;
}

export const AudioRecorder: React.FC<AudioRecorderProps> = ({ 
  onAudioMessage,
  isProcessing = false
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setAudioBlob(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      toast.error('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Stop all audio tracks
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const sendAudio = async () => {
    if (!audioBlob) return;

    try {
      // Convert blob to base64
      const reader = new FileReader();
      reader.readAsDataURL(audioBlob);
      reader.onloadend = () => {
        const base64data = reader.result as string;
        // Remove the data URL prefix (e.g., "data:audio/wav;base64,")
        const base64Audio = base64data.split(',')[1];
        onAudioMessage(base64Audio, 'wav');
        setAudioBlob(null);
      };
    } catch (error) {
      console.error('Error processing audio:', error);
      toast.error('Error processing audio');
    }
  };

  const cancelRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
      setAudioBlob(null);
    }
  };

  return (
    <div className="flex items-center space-x-2">
      {!isRecording && !audioBlob && (
        <Button
          type="button"
          size="icon"
          variant="ghost"
          className="rounded-full h-10 w-10 text-eva-purple hover:bg-eva-purple/10"
          onClick={startRecording}
          disabled={isProcessing}
        >
          <Mic className="h-5 w-5" />
        </Button>
      )}

      {isRecording && (
        <Button
          type="button"
          size="icon"
          variant="destructive"
          className="rounded-full h-10 w-10"
          onClick={stopRecording}
        >
          <Square className="h-5 w-5" />
        </Button>
      )}

      {audioBlob && !isRecording && (
        <>
          <Button
            type="button"
            size="icon"
            variant="ghost"
            className="rounded-full h-10 w-10 text-red-500 hover:bg-red-500/10"
            onClick={cancelRecording}
          >
            <Square className="h-5 w-5" />
          </Button>
          <Button
            type="button"
            size="icon"
            variant="ghost"
            className="rounded-full h-10 w-10 text-eva-purple hover:bg-eva-purple/10"
            onClick={sendAudio}
            disabled={isProcessing}
          >
            <Send className="h-5 w-5" />
          </Button>
        </>
      )}

      {isRecording && (
        <div className="text-sm text-eva-text-secondary animate-pulse">
          Recording...
        </div>
      )}
    </div>
  );
};

export default AudioRecorder;
