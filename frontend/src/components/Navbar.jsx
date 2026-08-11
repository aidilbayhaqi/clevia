import { Menu, X } from "../icons";
import { NavLink, Link } from "react-router-dom";
import { useState } from "react";
import Logo from "./Logo";
const links = [
  ["/", "Home"],
  ["/treatments", "Treatments"],
  ["/doctors", "Doctors"],
  ["/about", "About"],
  ["/contact", "Contact"],
];
export default function Navbar() {
  const [open, setOpen] = useState(false);
  return (
    <header className="nav">
      <div className="container nav__inner">
        <Logo />
        <nav className={open ? "nav__links is-open" : "nav__links"}>
          {links.map(([to, label]) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              onClick={() => setOpen(false)}
            >
              {label}
            </NavLink>
          ))}
          <Link
            to="/booking"
            className="btn btn--dark btn--small"
            onClick={() => setOpen(false)}
          >
            Book appointment
          </Link>
        </nav>
        <button
          className="nav__toggle"
          onClick={() => setOpen(!open)}
          aria-label="Menu"
        >
          {open ? <X /> : <Menu />}
        </button>
      </div>
    </header>
  );
}
