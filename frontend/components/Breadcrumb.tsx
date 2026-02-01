import Link from 'next/link';
import { ChevronRight, Home } from 'lucide-react';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

export default function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav className="flex items-center space-x-2 text-sm text-slate-400 mb-6" aria-label="Breadcrumb">
      <Link 
        href="/" 
        className="hover:text-emerald-400 transition-colors inline-flex items-center gap-1"
        aria-label="Home"
      >
        <Home size={16} />
        <span>Home</span>
      </Link>
      
      {items.map((item, index) => (
        <div key={index} className="flex items-center space-x-2">
          <ChevronRight size={16} className="text-slate-600" />
          {item.href ? (
            <Link 
              href={item.href} 
              className="hover:text-emerald-400 transition-colors"
            >
              {item.label}
            </Link>
          ) : (
            <span className="text-slate-300 font-medium">{item.label}</span>
          )}
        </div>
      ))}
    </nav>
  );
}
