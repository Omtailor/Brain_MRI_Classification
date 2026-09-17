import { Brain } from 'lucide-react';
import './Header.css';

/**
 * Header
 * Contains only the BrainScan AI logo/brand.
 * No navigation, login, or user elements (by design).
 */
export default function Header() {
  return (
    <header className="header" role="banner">
      <div className="header__inner container">
        {/* Brand */}
        <a className="header__brand" href="/" aria-label="BrainScan AI — Home">
          <span className="header__logo-wrap" aria-hidden="true">
            <Brain size={28} strokeWidth={1.8} />
          </span>
          <span className="header__brand-name">BrainScan AI</span>
        </a>
      </div>
    </header>
  );
}
