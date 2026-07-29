import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  ChevronDown,
  ClipboardCheck,
  Command,
  FileClock,
  FilePlus2,
  Files,
  Home,
  LogOut,
  Menu,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Shield,
  Sun,
  UserRound,
  UsersRound,
  X,
  type LucideIcon,
} from "lucide-react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../../auth/AuthProvider";
import { copy } from "../../content/uiCopy";
import { BrandMark } from "../product/BrandMark";
import { Button } from "../ui/Button";

type Role = "employee" | "reviewer" | "administrator";
type NavItem = { to: string; label: string; icon: LucideIcon; roles?: Role[] };
type NavGroup = { label: string; items: NavItem[]; roles?: Role[] };

const navGroups: NavGroup[] = [
  {
    label: copy.shell.workspaceGroup,
    items: [
      { to: "/", label: copy.nav.dashboard, icon: Home },
      { to: "/search", label: copy.nav.search, icon: Search },
    ],
  },
  {
    label: copy.shell.knowledgeGroup,
    items: [
      { to: "/solutions/new", label: copy.nav.submit, icon: FilePlus2 },
      { to: "/people/me", label: copy.nav.contributions, icon: Files },
      { to: "/drafts", label: copy.nav.drafts, icon: FileClock },
    ],
  },
  {
    label: copy.shell.collaborationGroup,
    items: [
      { to: "/reviews", label: copy.nav.reviews, icon: ClipboardCheck, roles: ["reviewer", "administrator"] },
      { to: "/people", label: copy.nav.people, icon: UsersRound },
    ],
  },
  {
    label: copy.shell.adminGroup,
    roles: ["administrator"],
    items: [{ to: "/admin/users", label: copy.nav.settings, icon: Shield, roles: ["administrator"] }],
  },
];

const routeTitles: Array<[RegExp, string]> = [
  [/^\/$/, copy.nav.dashboard],
  [/^\/search/, copy.nav.search],
  [/^\/solutions\/new/, copy.nav.submit],
  [/^\/solutions\/[^/]+\/edit/, copy.action.editSolution],
  [/^\/solutions\//, copy.page.solutionTitle],
  [/^\/drafts/, copy.nav.drafts],
  [/^\/reviews/, copy.nav.reviews],
  [/^\/people\//, copy.profile.title],
  [/^\/admin/, copy.nav.settings],
];

export function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(() => window.localStorage.getItem("resolve.sidebar") === "collapsed");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [userOpen, setUserOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    const saved = window.localStorage.getItem("resolve.theme");
    if (saved === "light" || saved === "dark") return saved;
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  const groups = useMemo(
    () => navGroups
      .filter((group) => !group.roles || (user && group.roles.includes(user.role)))
      .map((group) => ({ ...group, items: group.items.filter((item) => !item.roles || (user && item.roles.includes(user.role))) }))
      .filter((group) => group.items.length > 0),
    [user],
  );
  const items = groups.flatMap((group) => group.items);
  const pageTitle = routeTitles.find(([pattern]) => pattern.test(location.pathname))?.[1] ?? copy.app.name;

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandOpen(true);
      }
      if (event.key === "Escape") {
        setCommandOpen(false);
        setMobileOpen(false);
        setUserOpen(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("resolve.theme", theme);
  }, [theme]);

  useEffect(() => {
    window.localStorage.setItem("resolve.sidebar", collapsed ? "collapsed" : "expanded");
  }, [collapsed]);

  const navigateTo = (path: string) => {
    setCommandOpen(false);
    setMobileOpen(false);
    navigate(path);
  };

  return (
    <div className="min-h-screen bg-canvas text-text">
      <DesktopSidebar
        collapsed={collapsed}
        groups={groups}
        onCollapse={() => setCollapsed((value) => !value)}
        onLogout={() => void logout()}
        role={user?.role}
        userEmail={user?.email}
      />
      <div className={`min-h-screen transition-[padding] duration-220 ${collapsed ? "lg:pl-[68px]" : "lg:pl-[240px]"}`}>
        <TopBar
          dark={theme === "dark"}
          pageTitle={pageTitle}
          role={user?.role}
          userEmail={user?.email}
          userOpen={userOpen}
          onCommand={() => setCommandOpen(true)}
          onLogout={() => void logout()}
          onMenu={() => setMobileOpen(true)}
          onTheme={() => setTheme((value) => (value === "dark" ? "light" : "dark"))}
          onUser={() => setUserOpen((value) => !value)}
        />
        <main className="mx-auto w-full max-w-[1480px] px-4 py-5 sm:px-6 lg:px-7 lg:py-7">
          <Outlet />
        </main>
      </div>
      {mobileOpen && <MobileNavigation groups={groups} onClose={() => setMobileOpen(false)} onLogout={() => void logout()} />}
      {commandOpen && <CommandPalette items={items} onClose={() => setCommandOpen(false)} onNavigate={navigateTo} />}
    </div>
  );
}

function DesktopSidebar({ collapsed, groups, onCollapse, onLogout, role, userEmail }: { collapsed: boolean; groups: NavGroup[]; onCollapse: () => void; onLogout: () => void; role?: Role; userEmail?: string }) {
  return (
    <aside className={`fixed inset-y-0 left-0 z-30 hidden border-r border-border bg-surface/90 shadow-[8px_0_40px_rgb(15_23_42/0.035)] backdrop-blur-xl transition-[width] duration-220 lg:flex lg:flex-col ${collapsed ? "w-[68px]" : "w-[240px]"}`}>
      <div className={`flex h-[64px] items-center border-b border-border ${collapsed ? "justify-center px-3" : "px-3.5"}`}>
        <BrandMark compact={collapsed} />
        {!collapsed && (
          <button className="ml-auto grid h-9 w-9 shrink-0 place-items-center rounded-control text-text-muted transition-colors hover:bg-surface-muted hover:text-text" aria-label={copy.shell.collapseNavigation} onClick={onCollapse}>
            <PanelLeftClose className="h-[18px] w-[18px]" />
          </button>
        )}
      </div>
      {collapsed && (
        <button className="mx-auto mt-3 grid h-9 w-9 place-items-center rounded-control text-text-muted hover:bg-surface-muted hover:text-text" aria-label={copy.shell.expandNavigation} onClick={onCollapse}>
          <PanelLeftOpen className="h-[18px] w-[18px]" />
        </button>
      )}
      <NavGroups collapsed={collapsed} groups={groups} />
      <div className="border-t border-border p-3">
        <div className={`overflow-hidden rounded-app border border-border bg-surface-muted/55 ${collapsed ? "flex items-center justify-center p-2" : "flex items-center gap-3 p-3"}`}>
          <Avatar email={userEmail} />
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-semibold text-text">{userEmail?.split("@")[0]}</p>
              <p className="mt-0.5 truncate text-[11px] capitalize text-text-muted">{role}</p>
            </div>
          )}
          {!collapsed && (
            <button className="grid h-8 w-8 place-items-center rounded-control text-text-muted hover:bg-surface hover:text-danger" aria-label={copy.action.signOut} onClick={onLogout}>
              <LogOut className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </aside>
  );
}

function NavGroups({ collapsed = false, groups, mobile = false }: { collapsed?: boolean; groups: NavGroup[]; mobile?: boolean }) {
  return (
    <nav className={`flex-1 overflow-y-auto ${mobile ? "p-3" : collapsed ? "px-2 py-4" : "p-3"}`} aria-label={mobile ? copy.shell.mobileNavigation : copy.shell.primaryNavigation}>
      {groups.map((group) => (
        <div className="mb-5" key={group.label}>
          {!collapsed && <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-text-muted">{group.label}</p>}
          <div className="space-y-1">
            {group.items.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  className={({ isActive }) => `group relative flex items-center overflow-hidden rounded-control text-sm font-medium transition-all duration-160 ${mobile ? "h-11 px-3" : "h-10"} ${isActive ? "bg-brand-soft text-brand-strong shadow-sm" : "text-text-muted hover:bg-surface-muted hover:text-text"} ${collapsed ? "justify-center px-0" : "gap-3 px-3"}`}
                  key={item.to}
                  to={item.to}
                  title={collapsed ? item.label : undefined}
                >
                  {({ isActive }) => (
                    <>
                      {isActive && <span className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-primary" />}
                      <Icon className={`h-[17px] w-[17px] shrink-0 transition-transform duration-160 group-hover:scale-110 ${isActive ? "text-brand-strong" : ""}`} aria-hidden="true" />
                      {!collapsed && <span className="truncate">{item.label}</span>}
                    </>
                  )}
                </NavLink>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
}

function TopBar({ dark, onCommand, onLogout, onMenu, onTheme, onUser, pageTitle, role, userEmail, userOpen }: { dark: boolean; onCommand: () => void; onLogout: () => void; onMenu: () => void; onTheme: () => void; onUser: () => void; pageTitle: string; role?: Role; userEmail?: string; userOpen: boolean }) {
  return (
    <header className="sticky top-0 z-20 flex h-[64px] items-center gap-3 border-b border-border bg-surface/86 px-4 shadow-[0_8px_30px_rgb(15_23_42/0.035)] backdrop-blur-xl sm:px-6 lg:px-7">
      <button className="grid h-10 w-10 place-items-center rounded-control text-text-muted hover:bg-surface-muted lg:hidden" aria-label={copy.mobile.menu} onClick={onMenu}>
        <Menu className="h-5 w-5" />
      </button>
      <div className="hidden min-w-0 lg:block">
        <p className="truncate text-sm font-semibold text-text">{pageTitle}</p>
      </div>
      <button className="pressable ml-auto flex h-10 w-full max-w-xl items-center gap-3 rounded-control border border-input bg-surface px-3 text-left text-sm text-text-muted shadow-sm transition-all hover:border-border-strong hover:bg-elevated hover:shadow-soft sm:ml-4" onClick={onCommand}>
        <Search className="h-4 w-4" aria-hidden="true" />
        <span className="truncate">{copy.command.searchAnything}</span>
        <kbd className="ml-auto hidden rounded-md border border-border bg-surface-muted px-2 py-0.5 text-[10px] font-medium text-text-muted md:inline">{copy.command.shortcut}</kbd>
      </button>
      <button className="pressable grid h-10 w-10 shrink-0 place-items-center rounded-control text-text-muted hover:bg-surface-muted hover:text-text" aria-label={copy.shell.toggleTheme} onClick={onTheme}>
        {dark ? <Sun className="h-[18px] w-[18px]" /> : <Moon className="h-[18px] w-[18px]" />}
      </button>
      <div className="relative">
        <button className="pressable flex h-10 items-center gap-2 rounded-control border border-border bg-surface px-2 shadow-sm hover:border-border-strong hover:bg-surface-muted" aria-label={copy.shell.openUserMenu} onClick={onUser}>
          <Avatar email={userEmail} small />
          <ChevronDown className="hidden h-3.5 w-3.5 text-text-muted sm:block" />
        </button>
        {userOpen && (
          <div className="product-card absolute right-0 top-12 z-30 w-72 overflow-hidden rounded-dialog p-2 shadow-overlay">
            <div className="border-b border-border px-3 py-3">
              <p className="truncate text-sm font-semibold">{userEmail}</p>
              <p className="mt-1 text-xs capitalize text-text-muted">{role}</p>
            </div>
            <Link className="mt-2 flex h-10 w-full items-center gap-2 rounded-control px-3 text-sm text-text-muted hover:bg-surface-muted hover:text-text" to="/people/me" onClick={onUser}>
              <UserRound className="h-4 w-4" />Open profile
            </Link>
            <button className="mt-1 flex h-10 w-full items-center gap-2 rounded-control px-3 text-sm text-text-muted hover:bg-surface-muted hover:text-danger" onClick={onLogout}>
              <LogOut className="h-4 w-4" />{copy.action.signOut}
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

function Avatar({ email, small = false }: { email?: string; small?: boolean }) {
  return (
    <span className={`grid shrink-0 place-items-center rounded-full border border-primary/20 bg-brand-soft font-semibold text-brand-strong ${small ? "h-7 w-7 text-[10px]" : "h-9 w-9 text-xs"}`}>
      {email?.slice(0, 1).toUpperCase() ?? <UserRound className="h-4 w-4" />}
    </span>
  );
}

function MobileNavigation({ groups, onClose, onLogout }: { groups: NavGroup[]; onClose: () => void; onLogout: () => void }) {
  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      <button className="absolute inset-0 bg-text/35 backdrop-blur-[2px]" aria-label={copy.mobile.closeMenu} onClick={onClose} />
      <aside className="relative flex h-full w-[320px] max-w-[88vw] flex-col border-r border-border bg-surface shadow-overlay">
        <div className="flex h-[64px] items-center justify-between border-b border-border px-4">
          <BrandMark />
          <button className="grid h-10 w-10 place-items-center rounded-control text-text-muted hover:bg-surface-muted" aria-label={copy.mobile.closeMenu} onClick={onClose}>
            <X className="h-5 w-5" />
          </button>
        </div>
        <NavGroups groups={groups} mobile />
        <div className="border-t border-border p-3"><Button className="w-full" onClick={onLogout}><LogOut className="h-4 w-4" />{copy.action.signOut}</Button></div>
      </aside>
    </div>
  );
}

function CommandPalette({ items, onClose, onNavigate }: { items: NavItem[]; onClose: () => void; onNavigate: (path: string) => void }) {
  const [query, setQuery] = useState("");
  const filtered = items.filter((item) => item.label.toLowerCase().includes(query.toLowerCase()));
  function submit(event: FormEvent) {
    event.preventDefault();
    const trimmed = query.trim();
    if (trimmed.length >= 3) onNavigate(`/search?q=${encodeURIComponent(trimmed)}`);
  }
  return (
    <div className="fixed inset-0 z-50 grid place-items-start bg-text/35 px-4 pt-[12vh] backdrop-blur-[3px]" role="presentation" onMouseDown={onClose}>
      <section className="product-card w-full max-w-2xl overflow-hidden rounded-dialog shadow-overlay" aria-label={copy.command.title} role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
        <form className="flex items-center gap-3 border-b border-border px-4" onSubmit={submit}>
          <Command className="h-5 w-5 text-brand-strong" aria-hidden="true" />
          <input autoFocus className="h-14 w-full bg-transparent text-sm outline-none placeholder:text-text-muted" onChange={(event) => setQuery(event.target.value)} placeholder={copy.command.hint} value={query} />
          <button className="pressable grid h-9 w-9 place-items-center rounded-control text-text-muted hover:bg-surface-muted" aria-label={copy.action.close} onClick={onClose} type="button"><X className="h-4 w-4" /></button>
        </form>
        <div className="max-h-[420px] overflow-y-auto p-2">
          {query.trim().length >= 3 && (
            <button className="mb-1 flex h-11 w-full items-center gap-3 rounded-control bg-brand-soft px-3 text-left text-sm font-medium text-brand-strong" onClick={() => onNavigate(`/search?q=${encodeURIComponent(query.trim())}`)}>
              <Search className="h-4 w-4" />Search for "{query.trim()}"
            </button>
          )}
          <p className="px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-text-muted">Navigate</p>
          {filtered.map((item) => {
            const Icon = item.icon;
            return <button className="flex h-11 w-full items-center gap-3 rounded-control px-3 text-left text-sm text-text hover:bg-surface-muted" key={`${item.to}-${item.label}`} onClick={() => onNavigate(item.to)}><Icon className="h-4 w-4 text-text-muted" />{item.label}</button>;
          })}
          {filtered.length === 0 && query.trim().length < 3 && <p className="px-3 py-6 text-center text-sm text-text-muted">{copy.command.noResults}</p>}
        </div>
      </section>
    </div>
  );
}
