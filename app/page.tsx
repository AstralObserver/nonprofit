import Image from "next/image";
import Link from 'next/link';
import Calendar from 'react-calendar';

export default function Home() {
  return (
    <main className="min-h-screen bg-orange-100 text-white flex flex-col">
      {/* Navbar */}
      <nav className="flex items-center justify-between px-6 py-4 bg-gray-800 shadow-md">
        <div className="flex items-center space-x-3">
          <Image src="/icon.png" alt="Blue and orange phoenix rising from a white rose." width={48} height={48} />
          <Link href="/" className="text-2xl font-bold hover:underline">Collective Improvment Association</Link>
        </div>

        <div className="space-x-6">
          <Link href="/about" className="text-2xl hover:underline">About Us</Link>
          <Link href="/branch" className="text-2xl hover:underline">Branches</Link>
        </div>
      </nav>

      <section className="flex justify-center items-center py-12">
        <h1 className="text-6xl text-black font-semibold mb-4">Maricopa Events Calendar</h1>
      </section>

      <section className="flex flex-col lg:flex-row justify-center items-start gap-8 px-4">
        {/* Calendar Block */}
        <div className="bg-white text-black rounded-lg shadow-lg p-10 w-full max-w-3xl text-center text-lg">
          <h2 className="text-3xl font-semibold mb-4">Events</h2>
          <Calendar className="w-full text-xl [&>*]:space-y-4" />
        </div>
        </section>
      </main>
  );
}
