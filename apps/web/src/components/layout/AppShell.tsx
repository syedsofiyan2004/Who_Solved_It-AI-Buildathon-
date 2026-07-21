import { useEffect, useState } from "react";
import { ClipboardCheck, Command, FilePlus2, LayoutDashboard, Menu, Moon, PanelLeftClose, PanelLeftOpen, Search, Shield, Sun, UserRound, X, type LucideIcon } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../../auth/AuthProvider";
import { copy } from "../../content/uiCopy";
import { Button } from "../ui/Button";

type Role = "employee" | "reviewer" | "administrator";
type NavItem = { to: string; label: string; icon: LucideIcon; roles?: Role[] };

const navItems: NavItem[] = [
  { to: "/", label: copy.nav.dashboard, icon: LayoutDashboard },
  { to: "/search", label: copy.nav.search, icon: Search },
  { to: "/solutions/new", label: copy.nav.submit, icon: FilePlus2 },
  { to: "/reviews", label: copy.nav.reviews, icon: ClipboardCheck, roles: ["reviewer", "administrator"] },
  { to: "/people/me", label: copy.nav.profile, icon: UserRound },
  { to: "/admin/users", label: copy.nav.settings, icon: Shield, roles: ["administrator"] }
];

export function AppShell() {
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [dark, setDark] = useState(false);
  const navigate = useNavigate();
  const items = navItems.filter((item) => !item.roles || (user && item.roles.includes(user.role)));

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandOpen(true);
      }
      if (event.key === "Escape") {
        setCommandOpen(false);
        setMobileOpen(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    return () => { delete document.documentElement.dataset.theme; };
  }, [dark]);

  const navigateTo = (path: string) => {
    setCommandOpen(false);
    setMobileOpen(false);
    navigate(path);
  };

  return (
    <div className="min-h-screen bg-canvas text-text">
      <DesktopSidebar collapsed={collapsed} items={items} onCollapse={() => setCollapsed(!collapsed)} onLogout={() => void logout()} userEmail={user?.email} />
      <div className={`min-h-screen transition-[padding] duration-160 ${collapsed ? "lg:pl-16" : "lg:pl-60"}`}>
        <TopBar dark={dark} onCommand={() => setCommandOpen(true)} onMenu={() => setMobileOpen(true)} onTheme={() => setDark(!dark)} />
        <main className="mx-auto w-full max-w-[1120px] px-4 py-6 sm:px-6"><Outlet /></main>
      </div>
      {mobileOpen && <MobileNavigation items={items} onClose={() => setMobileOpen(false)} onLogout={() => void logout()} />}
      {commandOpen && <CommandPalette items={items} onClose={() => setCommandOpen(false)} onNavigate={navigateTo} />}
    </div>
  );
}

function DesktopSidebar({ collapsed, items, onCollapse, onLogout, userEmail }: { collapsed: boolean; items: NavItem[]; onCollapse: () => void; onLogout: () => void; userEmail?: string }) {
  return <aside className={`fixed inset-y-0 left-0 z-30 hidden border-r border-border bg-surface transition-[width] duration-160 lg:flex lg:flex-col ${collapsed ? "w-16" : "w-60"}`}><div className="flex h-14 items-center border-b border-border px-3"><span className={`truncate text-sm font-semibold ${collapsed ? "sr-only" : ""}`}>{copy.app.name}</span><button className="ml-auto grid h-9 w-9 place-items-center rounded-control text-text-muted hover:bg-surface-muted hover:text-text" aria-label={collapsed ? copy.shell.expandNavigation : copy.shell.collapseNavigation} onClick={onCollapse}>{collapsed ? <PanelLeftOpen className="h-5 w-5" /> : <PanelLeftClose className="h-5 w-5" />}</button></div><NavItems collapsed={collapsed} items={items} /><div className="border-t border-border p-2"><button className={`flex h-9 w-full items-center rounded-control text-left text-sm text-text-muted hover:bg-surface-muted hover:text-text ${collapsed ? "justify-center" : "px-3"}`} aria-label={copy.shell.openUserMenu} onClick={onLogout}>{collapsed ? userEmail?.slice(0, 1).toUpperCase() : <><span className="truncate">{userEmail}</span><span className="sr-only">{copy.action.signOut}</span></>}</button></div></aside>;
}

function NavItems({ collapsed = false, items, mobile = false }: { collapsed?: boolean; items: NavItem[]; mobile?: boolean }) {
  return <nav className={`flex-1 space-y-1 ${mobile ? "p-3" : "p-2"}`} aria-label={mobile ? copy.shell.mobileNavigation : copy.shell.primaryNavigation}>{items.map((item) => { const Icon = item.icon; return <NavLink className={({ isActive }) => `flex ${mobile ? "h-11 px-3" : "h-9 px-3"} items-center rounded-control text-sm font-medium transition-colors ${isActive ? "bg-surface-muted text-text" : "text-text-muted hover:bg-surface-muted hover:text-text"} ${collapsed ? "justify-center px-0" : "gap-3"}`} key={item.to} to={item.to} title={collapsed ? item.label : undefined}><Icon className="h-4 w-4 shrink-0" aria-hidden="true" />{!collapsed && item.label}</NavLink>; })}</nav>;
}

function TopBar({ dark, onCommand, onMenu, onTheme }: { dark: boolean; onCommand: () => void; onMenu: () => void; onTheme: () => void }) {
  return <header className="sticky top-0 z-20 flex h-14 items-center gap-2 border-b border-border bg-surface px-4 lg:px-6"><button className="grid h-10 w-10 place-items-center rounded-control text-text-muted hover:bg-surface-muted lg:hidden" aria-label={copy.mobile.menu} onClick={onMenu}><Menu className="h-5 w-5" /></button><button className="grid h-10 w-10 place-items-center rounded-control text-text-muted hover:bg-surface-muted sm:hidden" aria-label={copy.action.openSearch} onClick={onCommand}><Search className="h-5 w-5" /></button><Button className="hidden sm:inline-flex" onClick={onCommand}><Search className="h-4 w-4" aria-hidden="true" />{copy.action.openSearch}<kbd className="ml-2 hidden rounded border border-border px-1 text-xs text-text-muted md:inline">{copy.command.shortcut}</kbd></Button><button className="ml-auto grid h-9 w-9 place-items-center rounded-control text-text-muted hover:bg-surface-muted" aria-label={copy.shell.toggleTheme} onClick={onTheme}>{dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}</button></header>;
}

function MobileNavigation({ items, onClose, onLogout }: { items: NavItem[]; onClose: () => void; onLogout: () => void }) {
  return <div className="fixed inset-0 z-50 lg:hidden"><button className="absolute inset-0 bg-text/30" aria-label={copy.mobile.closeMenu} onClick={onClose} /><aside className="relative flex h-full w-72 flex-col bg-surface shadow-overlay"><div className="flex h-14 items-center justify-between border-b border-border px-4"><span className="text-sm font-semibold">{copy.app.name}</span><button className="grid h-10 w-10 place-items-center rounded-control text-text-muted hover:bg-surface-muted" aria-label={copy.mobile.closeMenu} onClick={onClose}><X className="h-5 w-5" /></button></div><NavItems items={items} mobile /><div className="border-t border-border p-3"><Button className="w-full" onClick={onLogout}>{copy.action.signOut}</Button></div></aside></div>;
}

function CommandPalette({ items, onClose, onNavigate }: { items: NavItem[]; onClose: () => void; onNavigate: (path: string) => void }) {
  return <div className="fixed inset-0 z-50 grid place-items-start bg-text/30 px-4 pt-[12vh]" role="presentation"><section className="w-full max-w-xl rounded-dialog border border-border bg-elevated shadow-overlay" aria-label={copy.command.title} role="dialog" aria-modal="true"><div className="flex items-center gap-3 border-b border-border px-4"><Command className="h-5 w-5 text-text-muted" aria-hidden="true" /><input autoFocus className="h-12 w-full bg-transparent text-sm outline-none placeholder:text-text-muted" placeholder={copy.command.hint} /><button className="grid h-9 w-9 place-items-center rounded-control text-text-muted hover:bg-surface-muted" aria-label={copy.action.close} onClick={onClose}><X className="h-4 w-4" /></button></div><div className="p-2">{items.map((item) => <button className="flex h-10 w-full items-center rounded-control px-3 text-left text-sm text-text hover:bg-surface-muted" key={item.to} onClick={() => onNavigate(item.to)}>{item.label}</button>)}</div></section></div>;
}
