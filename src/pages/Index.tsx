
import { Sidebar } from "@/components/chat/Sidebar";
import { ChatWindow } from "@/components/chat/ChatWindow";

const Index = () => {
  return (
    <>
      {/* Google Font Import */}
      <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap" />
      <div className="flex w-full min-h-screen bg-eva-bg text-eva-text-primary font-space">
        <Sidebar />
        <ChatWindow />
      </div>
    </>
  );
};

export default Index;
