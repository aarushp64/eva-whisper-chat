
import { Sidebar } from "@/components/chat/Sidebar";
import { ChatWindow } from "@/components/chat/ChatWindow";

const Index = () => {
  return (
    <div className="flex w-full min-h-screen bg-eva-bg text-eva-text-primary">
      <Sidebar />
      <ChatWindow />
    </div>
  );
};

export default Index;
