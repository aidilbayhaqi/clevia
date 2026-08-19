export type IconName =
  | "home" | "leads" | "clients" | "calendar" | "chat" | "book" | "settings"
  | "logout" | "menu" | "close" | "arrow" | "sparkle" | "clock" | "search"
  | "check" | "user" | "phone" | "mail" | "location";

const paths: Record<IconName, string> = {
  home: "M3 10.5 12 3l9 7.5V21a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1V10.5Z",
  leads: "M4 19v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2M10 9a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm8 3a3 3 0 1 0 0-6",
  clients: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm13 10v-2a4 4 0 0 0-3-3.87",
  calendar: "M4 5h16v16H4zM8 3v4m8-4v4M4 10h16",
  chat: "M21 15a4 4 0 0 1-4 4H8l-5 3 1.5-5A7 7 0 0 1 3 12V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v8Z",
  book: "M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5v14ZM4 5.5A2.5 2.5 0 0 1 6.5 8H20",
  settings: "M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Zm7.4-3.5a7.5 7.5 0 0 0-.08-1l2-1.56-2-3.46-2.48 1a8 8 0 0 0-1.72-1L14.75 3h-4l-.37 2.98a8 8 0 0 0-1.72 1l-2.48-1-2 3.46 2 1.56a7.5 7.5 0 0 0 0 2l-2 1.56 2 3.46 2.48-1a8 8 0 0 0 1.72 1L10.75 21h4l.37-2.98a8 8 0 0 0 1.72-1l2.48 1 2-3.46-2-1.56c.05-.33.08-.66.08-1Z",
  logout: "M10 17l5-5-5-5m5 5H3m11-9h6a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1h-6",
  menu: "M4 7h16M4 12h16M4 17h16",
  close: "m6 6 12 12M18 6 6 18",
  arrow: "M5 12h14m-5-5 5 5-5 5",
  sparkle: "m12 3 1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3Zm6 11 .8 2.2L21 17l-2.2.8L18 20l-.8-2.2L15 17l2.2-.8L18 14Z",
  clock: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Zm0-14v5l3 2",
  search: "m21 21-4.3-4.3M19 11a8 8 0 1 1-16 0 8 8 0 0 1 16 0Z",
  check: "m5 12 4 4L19 6",
  user: "M20 21a8 8 0 0 0-16 0m8-9a5 5 0 1 0 0-10 5 5 0 0 0 0 10Z",
  phone: "M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .35 2 .7 2.9a2 2 0 0 1-.45 2.1L8.1 10a16 16 0 0 0 6 6l1.3-1.25a2 2 0 0 1 2.1-.45c.9.35 1.9.6 2.9.7a2 2 0 0 1 1.6 1.9Z",
  mail: "M3 5h18v14H3zM3 7l9 6 9-6",
  location: "M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0Zm-8 3a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z",
};

export function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  return (
    <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d={paths[name]} />
    </svg>
  );
}
