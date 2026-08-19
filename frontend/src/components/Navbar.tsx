import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import Logo from "./Logo";
import { Icon } from "./Icon";

const links = [
  ["Treatments", "/treatments"],
  ["Doctors", "/doctors"],
  ["About", "/about"],
  ["Contact", "/contact"],
] as const;

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="public-nav">
      <div className="container public-nav__inner">
        <Logo />

        <nav className={open ? "public-nav__links is-open" : "public-nav__links"}>
          {links.map(([label, href]) => (
            <NavLink key={href} to={href} onClick={() => setOpen(false)}>
              {label}
            </NavLink>
          ))}
          <Link className="btn btn--gold mobile-only" to="/booking">
            Book consultation
          </Link>
        </nav>

        <div className="public-nav__actions">
          <Link className="staff-link desktop-only" to="/admin/login">
            Staff portal
          </Link>
          <Link className="btn btn--gold desktop-only" to="/booking">
            Book consultation <Icon name="arrow" />
          </Link>
          <button
            aria-label="Toggle navigation"
            className="icon-button mobile-only"
            onClick={() => setOpen((value) => !value)}
          >
            <Icon name={open ? "close" : "menu"} />
          </button>
        </div>
      </div>
    </header>
  );
}
