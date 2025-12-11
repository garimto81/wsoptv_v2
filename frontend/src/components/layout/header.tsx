'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Search, User, LogOut, Settings, Shield, ChevronDown, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';

// Category definitions
const CATEGORIES = [
  { id: 'all', name: 'All', href: '/browse' },
  { id: 'wsop', name: 'WSOP', href: '/browse?category=wsop' },
  { id: 'hcl', name: 'HCL', href: '/browse?category=hcl' },
  { id: 'ggmillions', name: 'GGMillions', href: '/browse?category=ggmillions' },
  { id: 'gog', name: 'GOG', href: '/browse?category=gog' },
  { id: 'mpp', name: 'MPP', href: '/browse?category=mpp' },
  { id: 'pad', name: 'PAD', href: '/browse?category=pad' },
];

interface HeaderProps {
  user?: {
    username?: string;
    email?: string;
    role: string;
  };
  onLogout?: () => void;
}

export function Header({ user, onLogout }: HeaderProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  // Track scroll for header background opacity
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
      setIsSearchOpen(false);
    }
  };

  const isAdmin = user?.role === 'admin';
  const displayName = user?.username || user?.email || 'User';

  return (
    <header
      className={cn(
        'fixed top-0 z-50 w-full transition-all duration-300',
        isScrolled
          ? 'bg-[#141414]'
          : 'bg-gradient-to-b from-black/80 via-black/50 to-transparent'
      )}
    >
      <div className="flex h-16 items-center px-4 md:px-12">
        {/* Logo */}
        <Link href="/browse" className="mr-8 flex items-center">
          <span className="text-[#E50914] font-bold text-2xl md:text-3xl tracking-tight">
            WSOPTV
          </span>
        </Link>

        {/* Category Navigation - Desktop */}
        <nav className="hidden md:flex items-center space-x-1">
          {CATEGORIES.map((category) => {
            const isActive =
              category.id === 'all'
                ? pathname === '/browse' && !pathname.includes('category=')
                : pathname.includes(`category=${category.id}`);

            return (
              <Link
                key={category.id}
                href={category.href}
                className={cn(
                  'px-3 py-2 text-sm font-medium rounded-md transition-colors',
                  isActive
                    ? 'text-white bg-white/10'
                    : 'text-gray-300 hover:text-white hover:bg-white/5'
                )}
              >
                {category.name}
              </Link>
            );
          })}
        </nav>

        {/* Category Navigation - Mobile Dropdown */}
        <div className="md:hidden">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="text-white">
                Browse <ChevronDown className="ml-1 h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="bg-[#141414] border-gray-800">
              {CATEGORIES.map((category) => (
                <DropdownMenuItem key={category.id} asChild>
                  <Link href={category.href} className="text-white hover:bg-white/10">
                    {category.name}
                  </Link>
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Right Section */}
        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="relative">
            {isSearchOpen ? (
              <form onSubmit={handleSearch} className="flex items-center">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    type="search"
                    placeholder="Titles, players..."
                    autoFocus
                    className="w-48 md:w-64 pl-10 pr-8 bg-[#141414] border-gray-600 text-white placeholder-gray-400 focus:border-white"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                  <button
                    type="button"
                    onClick={() => {
                      setIsSearchOpen(false);
                      setSearchQuery('');
                    }}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </form>
            ) : (
              <button
                onClick={() => setIsSearchOpen(true)}
                className="text-gray-300 hover:text-white transition-colors p-2"
              >
                <Search className="h-5 w-5" />
              </button>
            )}
          </div>

          {/* Admin Link (if admin) */}
          {isAdmin && (
            <Link
              href="/admin"
              className="hidden md:block text-gray-300 hover:text-white text-sm font-medium transition-colors"
            >
              Admin
            </Link>
          )}

          {/* User Menu */}
          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="relative h-8 w-8 rounded p-0 hover:bg-transparent"
                >
                  <Avatar className="h-8 w-8 rounded">
                    <AvatarFallback className="bg-[#E50914] text-white rounded text-sm">
                      {displayName.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <ChevronDown className="ml-1 h-4 w-4 text-white" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                className="w-56 bg-[#141414]/95 border-gray-800 backdrop-blur"
                align="end"
                forceMount
              >
                <div className="flex items-center gap-3 p-3 border-b border-gray-800">
                  <Avatar className="h-10 w-10 rounded">
                    <AvatarFallback className="bg-[#E50914] text-white rounded">
                      {displayName.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex flex-col">
                    <p className="text-white font-medium">{displayName}</p>
                    <p className="text-xs text-gray-400">
                      {user.role === 'admin' ? 'Administrator' : 'Member'}
                    </p>
                  </div>
                </div>

                <DropdownMenuItem asChild>
                  <Link
                    href="/profile"
                    className="cursor-pointer text-gray-300 hover:text-white hover:bg-white/10"
                  >
                    <User className="mr-2 h-4 w-4" />
                    Profile
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link
                    href="/settings"
                    className="cursor-pointer text-gray-300 hover:text-white hover:bg-white/10"
                  >
                    <Settings className="mr-2 h-4 w-4" />
                    Settings
                  </Link>
                </DropdownMenuItem>

                {isAdmin && (
                  <>
                    <DropdownMenuSeparator className="bg-gray-800" />
                    <DropdownMenuItem asChild>
                      <Link
                        href="/admin"
                        className="cursor-pointer text-gray-300 hover:text-white hover:bg-white/10"
                      >
                        <Shield className="mr-2 h-4 w-4" />
                        Admin Dashboard
                      </Link>
                    </DropdownMenuItem>
                  </>
                )}

                <DropdownMenuSeparator className="bg-gray-800" />
                <DropdownMenuItem
                  className="cursor-pointer text-gray-300 hover:text-white hover:bg-white/10"
                  onClick={onLogout}
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button
              asChild
              className="bg-[#E50914] hover:bg-[#F40612] text-white border-none"
              size="sm"
            >
              <Link href="/login">Sign In</Link>
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;
