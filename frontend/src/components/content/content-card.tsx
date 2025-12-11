'use client';

import { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Play, Plus, ThumbsUp, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Content, WatchProgress } from '@/types/api';

interface ContentCardProps {
  content: Content;
  progress?: WatchProgress;
  className?: string;
  variant?: 'default' | 'compact' | 'large';
  showRank?: number;
}

export function ContentCard({
  content,
  progress,
  className,
  variant = 'default',
  showRank,
}: ContentCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const progressPercentage = progress?.percentage ?? 0;

  return (
    <div
      className={cn(
        'relative group/card flex-shrink-0 cursor-pointer',
        variant === 'compact' && 'w-[160px] md:w-[200px]',
        variant === 'default' && 'w-[200px] md:w-[240px]',
        variant === 'large' && 'w-[280px] md:w-[320px]',
        className
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Rank Number for TOP 10 */}
      {showRank && (
        <div className="absolute -left-8 md:-left-12 top-0 bottom-0 flex items-center pointer-events-none z-0">
          <span
            className="text-[80px] md:text-[120px] font-black leading-none"
            style={{
              WebkitTextStroke: '2px #808080',
              WebkitTextFillColor: 'transparent',
              textShadow: '4px 4px 8px rgba(0,0,0,0.5)',
            }}
          >
            {showRank}
          </span>
        </div>
      )}

      {/* Card Container */}
      <div
        className={cn(
          'relative rounded overflow-hidden bg-[#181818] transition-all duration-300 ease-out',
          isHovered && 'scale-[1.3] z-50 shadow-2xl shadow-black/80',
          showRank && 'ml-8 md:ml-12'
        )}
      >
        <Link href={`/watch/${content.id}`}>
          {/* Thumbnail */}
          <div className="relative aspect-video bg-gradient-to-br from-gray-700 to-gray-900">
            {content.thumbnail_url ? (
              <Image
                src={content.thumbnail_url}
                alt={content.title}
                fill
                className="object-cover"
                sizes="(max-width: 768px) 200px, 240px"
              />
            ) : (
              <div className="flex h-full items-center justify-center">
                <Play className="h-10 w-10 text-white/30" />
              </div>
            )}

            {/* Category Badge */}
            {content.category && (
              <div className="absolute top-2 left-2 px-2 py-0.5 bg-[#E50914] text-white text-xs font-semibold rounded">
                {content.category}
              </div>
            )}

            {/* Duration Badge */}
            <div className="absolute bottom-2 right-2 px-2 py-0.5 bg-black/80 text-white text-xs rounded">
              {formatDuration(content.duration_seconds)}
            </div>

            {/* Hover Play Icon Overlay */}
            <div
              className={cn(
                'absolute inset-0 flex items-center justify-center bg-black/30 transition-opacity duration-200',
                isHovered ? 'opacity-100' : 'opacity-0'
              )}
            >
              <div className="w-12 h-12 rounded-full bg-white/90 flex items-center justify-center">
                <Play className="h-6 w-6 text-black fill-current ml-1" />
              </div>
            </div>
          </div>
        </Link>

        {/* Progress Bar */}
        {progressPercentage > 0 && (
          <div className="h-1 bg-gray-700">
            <div
              className="h-full bg-[#E50914] transition-all"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        )}

        {/* Expanded Info Panel (on hover) */}
        <div
          className={cn(
            'bg-[#181818] transition-all duration-300 overflow-hidden',
            isHovered ? 'max-h-[200px] opacity-100 p-3' : 'max-h-0 opacity-0 p-0'
          )}
        >
          {/* Action Buttons */}
          <div className="flex items-center gap-2 mb-3">
            <Link
              href={`/watch/${content.id}`}
              className="w-9 h-9 rounded-full bg-white flex items-center justify-center hover:bg-white/80 transition-colors"
            >
              <Play className="h-5 w-5 text-black fill-current ml-0.5" />
            </Link>
            <button
              className="w-9 h-9 rounded-full border-2 border-gray-400 flex items-center justify-center hover:border-white transition-colors"
              title="Add to My List"
            >
              <Plus className="h-5 w-5 text-white" />
            </button>
            <button
              className="w-9 h-9 rounded-full border-2 border-gray-400 flex items-center justify-center hover:border-white transition-colors"
              title="Like"
            >
              <ThumbsUp className="h-4 w-4 text-white" />
            </button>
            <div className="flex-1" />
            <button
              className="w-9 h-9 rounded-full border-2 border-gray-400 flex items-center justify-center hover:border-white transition-colors"
              title="More Info"
            >
              <ChevronDown className="h-5 w-5 text-white" />
            </button>
          </div>

          {/* Title */}
          <h3 className="text-white text-sm font-semibold line-clamp-1 mb-1">
            {content.title}
          </h3>

          {/* Metadata Row */}
          <div className="flex items-center gap-2 text-xs mb-2">
            {content.year && (
              <span className="text-[#46D369] font-medium">{content.year}</span>
            )}
            {content.duration_seconds && (
              <span className="text-gray-400">{formatDuration(content.duration_seconds)}</span>
            )}
            {content.quality && (
              <span className="px-1 border border-gray-500 text-gray-400 text-[10px]">
                {content.quality}
              </span>
            )}
          </div>

          {/* Progress Info */}
          {progressPercentage > 0 && (
            <p className="text-xs text-gray-500">{Math.round(progressPercentage)}% watched</p>
          )}

          {/* Tags */}
          {content.tags && content.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {content.tags.slice(0, 3).map((tag, idx) => (
                <span key={tag} className="text-[10px] text-gray-400">
                  {tag}
                  {idx < Math.min(content.tags!.length, 3) - 1 && (
                    <span className="mx-1 text-gray-600">•</span>
                  )}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ContentCard;
