import { Instagram, MapPin, Phone, Mail, ArrowUpRight } from "../icons";
import { Link } from "react-router-dom";
import Logo from "./Logo";
export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer__grid">
        <div>
          <Logo dark />
          <p>
            Beauty care yang terasa personal, tenang, dan tetap berpijak pada
            keputusan klinis.
          </p>
        </div>
        <div>
          <h4>Explore</h4>
          <Link to="/treatments">Treatments</Link>
          <Link to="/doctors">Doctors</Link>
          <Link to="/booking">Appointment</Link>
          <Link to="/about">About Clevia</Link>
        </div>
        <div>
          <h4>Visit us</h4>
          <p>
            <MapPin /> Jakarta, Indonesia
          </p>
          <p>
            <Phone /> +62 21 5550 2026
          </p>
          <p>
            <Mail /> hello@clevia.example
          </p>
        </div>
        <div>
          <h4>Social</h4>
          <a href="#">
            <Instagram /> @cleviabeauty <ArrowUpRight />
          </a>
        </div>
      </div>
      <div className="container footer__bottom">
        <span>© 2026 Clevia Beauty Clinic.</span>
        <span>Confidence, refined.</span>
      </div>
    </footer>
  );
}
