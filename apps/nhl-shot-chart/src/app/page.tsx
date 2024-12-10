import NHLEdgeHockeyRink from '@/components/nhl-edge-hockey-rink/nhl-edge-hockey-rink';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center p-4 sm:p-8 md:p-12">
      <div className="w-full max-w-7xl space-y-6">
        <h1 className="text-4xl font-bold text-center">Sploosh.AI NHL Shot Chart</h1>
        <div className="flex justify-center items-center w-full h-full">
          <NHLEdgeHockeyRink className="w-full h-auto" />
        </div>
      </div>
    </main>
  );
} 