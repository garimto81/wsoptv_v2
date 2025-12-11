'use client';

import { useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, Play, Plus, ThumbsUp } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Progress } from '@/components/ui/progress';

interface ContentItem {
  id: string;
  title: string;
  thumbnail?: string;
  category?: string;
  year?: number;
  duration?: string;
  progress?: number; // 0-100 for continue watching
  rank?: number; // For TOP 10
}

interface ContentRowProps {
  title: string;
  items: ContentItem[];
  variant?: 'default' | 'continue-watching' | 'top10';
  showRank?: boolean;
}

// Mock data generator
function generateMockItems(count: number, variant: string): ContentItem[] {
  const categories = ['WSOP', 'HCL', 'GGMillions', 'GOG', 'MPP', 'PAD'];
  const players = ['Phil Ivey', 'Daniel Negreanu', 'Tom Dwan', 'Doug Polk', 'Phil Hellmuth'];

  return Array.from({ length: count }, (_, i) => ({
    id: `${variant}-${i + 1}`,
    title: variant === 'top10'
      ? `${players[i % players.length]} - ${['Epic Bluff', 'All-in Call', 'Cooler Hand', 'Monster Pot', 'Final Table'][i % 5]}`
      : `${categories[i % categories.length]} ${2024 - (i % 3)} - Episode ${i + 1}`,
    category: categories[i % categories.length],
    year: 2024 - (i % 3),
    duration: `${Math.floor(Math.random() * 3) + 1}h ${Math.floor(Math.random() * 59)}m`,
    progress: variant === 'continue-watching' ? Math.floor(Math.random() * 90) + 5 : undefined,
    rank: variant === 'top10' ? i + 1 : undefined,
  }));
}

export function ContentRow({ title, items, variant = 'default', showRank = false }: ContentRowProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(true);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const scroll = (direction: 'left' | 'right') => {
    if (!scrollRef.current) return;

    const scrollAmount = scrollRef.current.clientWidth * 0.8;
    const newScrollLeft = scrollRef.current.scrollLeft + (direction === 'left' ? -scrollAmount : scrollAmount);

    scrollRef.current.scrollTo({
      left: newScrollLeft,
      behavior: 'smooth',
    });
  };

  const handleScroll = () => {
    if (!scrollRef.current) return;

    const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
    setShowLeftArrow(scrollLeft > 20);
    setShowRightArrow(scrollLeft < scrollWidth - clientWidth - 20);
  };

  const displayItems = items.length > 0 ? items : generateMockItems(10, variant);

  return (
    <section className="relative px-4 md:px-12 mb-8 group/row">
      {/* Row Title */}
      <h2 className="text-lg md:text-xl font-semibold text-white mb-3 flex items-center gap-2">
        {variant === 'top10' && <span className="text-[#E50914]">TOP 10</span>}
        {title}
        <ChevronRight className="h-5 w-5 text-[#E50914] opacity-0 group-hover/row:opacity-100 transition-opacity" />
      </h2>

      {/* Scroll Container */}
      <div className="relative -mx-4 md:-mx-12">
        {/* Left Arrow */}
        {showLeftArrow && (
          <button
            onClick={() => scroll('left')}
            className="absolute left-0 top-0 bottom-0 z-20 w-12 md:w-16 bg-gradient-to-r from-[#141414] to-transparent flex items-center justify-start pl-2 opacity-0 group-hover/row:opacity-100 transition-opacity"
          >
            <ChevronLeft className="h-8 w-8 text-white" />
          </button>
        )}

        {/* Content Slider */}
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className="flex gap-2 overflow-x-auto scrollbar-hide scroll-smooth px-4 md:px-12"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          {displayItems.map((item, index) => (
            <div
              key={item.id}
              className={cn(
                'flex-shrink-0 relative group/card transition-all duration-300',
                variant === 'top10' ? 'w-[200px] md:w-[280px]' : 'w-[160px] md:w-[220px]',
                hoveredId === item.id && 'z-30 scale-110'
              )}
              onMouseEnter={() => setHoveredId(item.id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              {/* TOP 10 Rank Number */}
              {variant === 'top10' && item.rank && (
                <div className="absolute -left-4 md:-left-8 top-0 bottom-0 flex items-center pointer-events-none">
                  <span
                    className="text-[100px] md:text-[140px] font-black leading-none"
                    style={{
                      WebkitTextStroke: '2px #E5E5E5',
                      WebkitTextFillColor: 'transparent',
                      textShadow: '4px 4px 8px rgba(0,0,0,0.5)',
                    }}
                  >
                    {item.rank}
                  </span>
                </div>
              )}

              {/* Card */}
              <Link
                href={`/watch/${item.id}`}
                className={cn(
                  'block rounded overflow-hidden bg-[#181818] transition-all duration-300',
                  variant === 'top10' && 'ml-12 md:ml-16'
                )}
              >
                {/* Thumbnail */}
                <div className="relative aspect-video bg-gradient-to-br from-gray-700 to-gray-900">
                  {/* Placeholder pattern */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Play className="h-10 w-10 text-white/30" />
                  </div>

                  {/* Category Badge */}
                  {item.category && (
                    <div className="absolute top-2 left-2 px-2 py-0.5 bg-[#E50914] text-white text-xs font-semibold rounded">
                      {item.category}
                    </div>
                  )}

                  {/* Hover Overlay */}
                  <div className="absolute inset-0 bg-black/0 group-hover/card:bg-black/30 transition-all duration-300" />
                </div>

                {/* Progress Bar (Continue Watching) */}
                {variant === 'continue-watching' && item.progress !== undefined && (
                  <div className="relative h-1 bg-gray-700">
                    <div
                      className="absolute top-0 left-0 h-full bg-[#E50914]"
                      style={{ width: `${item.progress}%` }}
                    />
                  </div>
                )}

                {/* Hover Info Panel */}
                <div
                  className={cn(
                    'bg-[#181818] p-3 transition-all duration-300',
                    hoveredId === item.id ? 'opacity-100' : 'opacity-0 h-0 p-0 overflow-hidden'
                  )}
                >
                  {/* Action Buttons */}
                  <div className="flex items-center gap-2 mb-2">
                    <button className="w-8 h-8 rounded-full bg-white flex items-center justify-center hover:bg-white/80">
                      <Play className="h-4 w-4 text-black fill-current ml-0.5" />
                    </button>
                    <button className="w-8 h-8 rounded-full border-2 border-gray-400 flex items-center justify-center hover:border-white">
                      <Plus className="h-4 w-4 text-white" />
                    </button>
                    <button className="w-8 h-8 rounded-full border-2 border-gray-400 flex items-center justify-center hover:border-white">
                      <ThumbsUp className="h-4 w-4 text-white" />
                    </button>
                  </div>

                  {/* Title */}
                  <h3 className="text-white text-sm font-medium line-clamp-1 mb-1">
                    {item.title}
                  </h3>

                  {/* Metadata */}
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    {item.year && <span className="text-[#46D369]">{item.year}</span>}
                    {item.duration && <span>{item.duration}</span>}
                  </div>

                  {/* Progress Text */}
                  {variant === 'continue-watching' && item.progress !== undefined && (
                    <p className="text-xs text-gray-500 mt-1">{item.progress}% watched</p>
                  )}
                </div>
              </Link>
            </div>
          ))}
        </div>

        {/* Right Arrow */}
        {showRightArrow && (
          <button
            onClick={() => scroll('right')}
            className="absolute right-0 top-0 bottom-0 z-20 w-12 md:w-16 bg-gradient-to-l from-[#141414] to-transparent flex items-center justify-end pr-2 opacity-0 group-hover/row:opacity-100 transition-opacity"
          >
            <ChevronRight className="h-8 w-8 text-white" />
          </button>
        )}
      </div>
    </section>
  );
}

export default ContentRow;
