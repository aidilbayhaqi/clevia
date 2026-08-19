import { Link } from "react-router-dom";
import Logo from "./Logo";
import { usePublicData } from "../context/PublicDataContext";

export default function Footer() {
  const { clinic } = usePublicData();

  return (
    <footer className="footer">
      <div className="container footer__grid">
        <div className="footer__brand">
          <Logo />
          <p>
            Thoughtful aesthetic care with clearer information, measured treatment
            planning, and human oversight where it matters.
          </p>
        </div>

        <div>
          <b>Explore</b>
          <Link to="/treatments">Treatments</Link>
          <Link to="/doctors">Doctors</Link>
          <Link to="/booking">Book consultation</Link>
        </div>

        <div>
          <b>Clevia</b>
          <Link to="/about">Our philosophy</Link>
          <Link to="/contact">Contact</Link>
          <Link to="/admin/login">Staff portal</Link>
        </div>

        <div>
          <b>Visit us</b>
          <span>{clinic?.address || "Jakarta, Indonesia"}</span>
          <span>{clinic?.phone || "Contact clinic"}</span>
          <span>{clinic?.instagram || "@cleviabeauty"}</span>
        </div>
      </div>

      <div className="container footer__bottom">
        <span>© 2026 Clevia Beauty Clinic</span>
        <span>Clinically considered · AI-assisted · Human-controlled</span>
      </div>
    </footer>
  );
}
