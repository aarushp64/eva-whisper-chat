
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Circle, Mic, MicOff } from "lucide-react";

export const ChatWindow = () => {
  const [inputValue, setInputValue] = useState("");
  const [isListening, setIsListening] = useState(false);

  const toggleMic = () => {
    setIsListening(!isListening);
    // We'll implement voice functionality in the next step
    console.log("Mic toggled:", !isListening);
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-eva-bg">
      {/* Status bar */}
      <div className="p-4 border-b border-eva-border flex items-center">
        <Circle className="w-3 h-3 text-green-500 mr-2" />
        <span className="text-eva-text-secondary text-sm">Online</span>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Assistant message */}
        <div className="flex items-start max-w-[80%] animate-fade-in">
          <div className="bg-eva-message-bubble rounded-2xl p-4 text-eva-text-primary">
            Hi, I'm EVA! How can I assist you today?
          </div>
        </div>
      </div>

      {/* Input area */}
      <div className="p-4 border-t border-eva-border bg-eva-panel">
        <form 
          className="flex items-center space-x-2"
          onSubmit={(e) => {
            e.preventDefault();
            console.log("Message sent:", inputValue);
            setInputValue("");
          }}
        >
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 bg-eva-bg text-eva-text-primary border-eva-border placeholder:text-eva-text-secondary"
          />
          <Button 
            type="button"
            onClick={toggleMic}
            variant="outline"
            className={`border-eva-border ${
              isListening 
                ? "bg-eva-purple text-white hover:bg-eva-purple-hover" 
                : "bg-eva-bg text-eva-text-primary hover:bg-eva-panel"
            }`}
          >
            {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </Button>
          <Button 
            type="submit"
            className="bg-eva-purple hover:bg-eva-purple-hover text-white"
          >
            Send
          </Button>
        </form>
      </div>
    </div>
  );
};
