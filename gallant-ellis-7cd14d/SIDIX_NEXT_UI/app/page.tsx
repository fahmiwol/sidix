import LeftSidebar from "@/components/LeftSidebar";
import ChatDashboard from "@/components/ChatDashboard";
import RightPanel from "@/components/RightPanel";

export default function HomePage() {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-sidix-darker">
      <LeftSidebar />
      <main className="flex-1 relative overflow-hidden">
        <ChatDashboard />
      </main>
      <RightPanel />
    </div>
  );
}
