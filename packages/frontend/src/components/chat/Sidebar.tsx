
import { Button } from "@/components/ui/button";
import { PlusCircle } from "lucide-react";

export const Sidebar = () => {
  return (
    <div className="w-64 bg-eva-panel border-r border-eva-border h-screen flex flex-col p-4 font-space">
      <div className="flex items-center space-x-3 mb-8">
        <div className="w-10 h-10 rounded-full bg-eva-purple flex items-center justify-center">
          <span className="text-white font-medium">EVA</span>
        </div>
        <div className="text-eva-text-primary font-medium">EVA Assistant</div>
      </div>
      
      <Button 
        className="bg-eva-purple hover:bg-eva-purple-hover text-white w-full mb-4"
        onClick={() => console.log("New chat")}
      >
        <PlusCircle className="w-4 h-4 mr-2" />
        New Chat
      </Button>
      
      <div className="flex-1 overflow-y-auto">
        {/* Chat history will go here */}
      </div>
    </div>
  );
};
