'use client';

import { useState, useEffect } from 'react';
import { Play, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

interface FeaturedContent {
  id: string;
  title: string;
  description: string;
  category: string;
  thumbnail?: string;
  backdropUrl?: string;
  year?: number;
  duration?: string;
  tags?: string[];
}

interface HeroBillboardProps {
  content?: FeaturedContent;
  onPlayClick?: (id: string) => void;
  onInfoClick?: (id: string) => void;
}

// Mock featured content for demo
const MOCK_FEATURED: FeaturedContent = {
  id: '1',
  title: 'WSOP 2024 Main Event Final Table',
  description:
    'Phil Ivey vs Daniel Negreanu - $10M 팟의 역대급 블러프. 포커 역사상 가장 드라마틱한 순간을 목격하세요.',
  category: 'WSOP',
  year: 2024,
  duration: '4h 32m',
  tags: ['Main Event', 'Final Table', 'Phil Ivey', 'Daniel Negreanu'],
};

export function HeroBillboard({
  content = MOCK_FEATURED,
  onPlayClick,
  onInfoClick,
}: HeroBillboardProps) {
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    setIsLoaded(true);
  }, []);

  return (
    <section className="relative h-[56.25vw] max-h-[80vh] min-h-[400px] w-full overflow-hidden">
      {/* Background Image/Video Placeholder */}
      <div className="absolute inset-0 bg-gradient-to-r from-[#141414] via-[#1a1a2e] to-[#16213e]">
        {/* Placeholder pattern for demo */}
        <div className="absolute inset-0 opacity-30">
          <div
            className="w-full h-full"
            style={{
              backgroundImage: `
                linear-gradient(45deg, #1a1a2e 25%, transparent 25%),
                linear-gradient(-45deg, #1a1a2e 25%, transparent 25%),
                linear-gradient(45deg, transparent 75%, #1a1a2e 75%),
                linear-gradient(-45deg, transparent 75%, #1a1a2e 75%)
              `,
              backgroundSize: '20px 20px',
              backgroundPosition: '0 0, 0 10px, 10px -10px, -10px 0px',
            }}
          />
        </div>

        {/* Poker table visual element */}
        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-1/2 h-2/3 opacity-20">
          <div className="w-full h-full rounded-full bg-gradient-to-br from-green-800 to-green-900 blur-3xl" />
        </div>
      </div>

      {/* Left Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-r from-[#141414] via-[#141414]/60 to-transparent" />

      {/* Bottom Gradient (for row transition) */}
      <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-[#141414] to-transparent" />

      {/* Content */}
      <div
        className={`absolute bottom-[15%] left-4 md:left-12 max-w-xl md:max-w-2xl transition-all duration-700 ${
          isLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        }`}
      >
        {/* Category Tag */}
        <div className="flex items-center gap-2 mb-4">
          <span className="text-[#E50914] font-bold text-sm tracking-widest">
            WSOPTV ORIGINAL
          </span>
        </div>

        {/* Title */}
        <h1 className="text-3xl md:text-5xl lg:text-6xl font-bold text-white mb-4 leading-tight">
          {content.title}
        </h1>

        {/* Metadata */}
        <div className="flex items-center gap-3 text-gray-400 text-sm mb-4">
          {content.year && <span className="text-[#46D369] font-semibold">{content.year}</span>}
          {content.duration && <span>{content.duration}</span>}
          {content.category && (
            <span className="px-2 py-0.5 border border-gray-600 rounded text-xs">
              {content.category}
            </span>
          )}
        </div>

        {/* Description */}
        <p className="text-gray-300 text-base md:text-lg mb-6 line-clamp-3">{content.description}</p>

        {/* Tags */}
        {content.tags && content.tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-6">
            {content.tags.slice(0, 4).map((tag) => (
              <span
                key={tag}
                className="text-xs text-gray-400 bg-white/10 px-2 py-1 rounded"
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <Button
            asChild
            className="bg-white hover:bg-white/90 text-black font-semibold px-6 py-6 text-lg"
          >
            <Link href={`/watch/${content.id}`}>
              <Play className="mr-2 h-6 w-6 fill-current" />
              Play
            </Link>
          </Button>

          <Button
            variant="outline"
            className="bg-gray-500/40 hover:bg-gray-500/60 text-white border-none px-6 py-6 text-lg"
            onClick={() => onInfoClick?.(content.id)}
          >
            <Info className="mr-2 h-6 w-6" />
            More Info
          </Button>
        </div>
      </div>

      {/* Mute/Volume button placeholder (Netflix style) */}
      <div className="absolute bottom-[15%] right-4 md:right-12 flex items-center gap-4">
        <div className="px-3 py-1 border-l-4 border-white/60 bg-gray-800/60 text-gray-300 text-sm">
          18+
        </div>
      </div>
    </section>
  );
}

export default HeroBillboard;
