import React, { useState, useEffect, useRef } from "react";
import { Mic, Volume2, VolumeX } from "lucide-react";
import { Socket } from "socket.io-client";
import { useToast } from "@/hooks/use-toast";
import { LLMConfig } from "./LLMSettingsModal";
import { Switch } from "@/components/ui/switch";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface VoiceControlsProps {
  socket: Socket;
  llmConfig: LLMConfig | null;
  setLlmConfig: (cfg: LLMConfig | null) => void;
}

export function VoiceControls({ socket, llmConfig, setLlmConfig }: VoiceControlsProps) {
  const [recording, setRecording] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(false); // we'll default to false for TTS unless turned on
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const { toast } = useToast();

  const toggleRecording = async () => {
    if (recording) {
      mediaRecorderRef.current?.stop();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => audioChunksRef.current.push(e.data);
      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        const configWithTTS = llmConfig ? { ...llmConfig, enableTTS: ttsEnabled } : { enableTTS: ttsEnabled };
        socket.emit("voice_message", { audioBlob: blob, llmConfig: configWithTTS });
        setRecording(false);
        stream.getTracks().forEach((track) => track.stop());
      };
      recorder.start();
      setRecording(true);
    } catch (e) {
      console.error("[VoiceControls] Mic error:", e);
      toast({ title: "Mic Error", description: "Unable to access microphone.", variant: "destructive" });
    }
  };

  const handleTtsToggle = (enabled: boolean) => {
    setTtsEnabled(enabled);
    if (llmConfig) {
      setLlmConfig({ ...llmConfig, enableTTS: enabled } as LLMConfig & { enableTTS: boolean });
    }
  };

  useEffect(() => {
    if (!socket) return;
    const handleChunk = ({ audioBase64 }: { audioBase64: string }) => {
      try {
        const binaryString = atob(audioBase64);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        
        // Use webm or just pass the generic content if unknown. Edge-TTS sends mp3 or pcm. 
        // For our backend, edge-tts gives stream arraybuffers. We default to generic audio type to let browser guess.
        const blob = new Blob([bytes.buffer], { type: "audio/mp3" });
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.play().catch((e) => console.error("[VoiceControls] Playback error:", e));
        audio.onended = () => URL.revokeObjectURL(url);
      } catch (err) {
        console.error("Failed to play back chunk", err);
      }
    };
    socket.on("tts_chunk", handleChunk);
    return () => {
      socket.off("tts_chunk", handleChunk);
    };
  }, [socket]);

  return (
    <div className="flex items-center gap-4">
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={toggleRecording}
              className={`p-2 rounded-full transition-colors ${
                recording ? "bg-red-500/20 text-red-500 animate-pulse" : "bg-eva-primary/20 text-eva-primary hover:bg-eva-primary/30"
              }`}
            >
              <Mic size={20} />
            </button>
          </TooltipTrigger>
          <TooltipContent>
            <p>{recording ? "Stop recording" : "Start voice input"}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="flex items-center gap-2">
              {ttsEnabled ? <Volume2 size={20} className="text-green-500" /> : <VolumeX size={20} className="text-gray-400" />}
              <Switch checked={ttsEnabled} onCheckedChange={handleTtsToggle} />
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <p>{ttsEnabled ? "TTS enabled" : "TTS disabled"}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  );
}
