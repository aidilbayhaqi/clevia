import { usePublicData } from "../../context/PublicDataContext";
import { WHATSAPP_NUMBER } from "../../config";
import { ErrorState, LoadingState } from "../../components/Ui";
import { Icon } from "../../components/Icon";

export default function ContactPage() {
  const { clinic, loading, error } = usePublicData();

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <>
      <section className="page-hero page-hero--gold">
        <div className="container">
          <span className="gold-pill">Contact Clevia</span>
          <h1>Need a human?<br /><em>We are easy to reach.</em></h1>
          <p>
            Untuk perubahan appointment, konfirmasi, dan pertanyaan yang membutuhkan
            staff, gunakan kanal resmi klinik.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="container contact-grid contact-grid--gold">
          <a
            className="contact-card contact-card--gold"
            href={`https://wa.me/${WHATSAPP_NUMBER}`}
            target="_blank"
            rel="noreferrer"
          >
            <Icon name="phone" />
            <span>WhatsApp / Phone</span>
            <b>{clinic?.phone || "Contact clinic"}</b>
            <small>Fastest operational channel</small>
          </a>

          <a
            className="contact-card contact-card--gold"
            href={`mailto:${clinic?.email || ""}`}
          >
            <Icon name="mail" />
            <span>Email</span>
            <b>{clinic?.email || "Email clinic"}</b>
            <small>Non-urgent communication</small>
          </a>

          <article className="contact-card contact-card--gold">
            <Icon name="location" />
            <span>Clinic location</span>
            <b>{clinic?.address || "Jakarta, Indonesia"}</b>
            <small>Please confirm your visit first</small>
          </article>

          <article className="contact-card contact-card--gold">
            <Icon name="sparkle" />
            <span>Instagram</span>
            <b>{clinic?.instagram || "@cleviabeauty"}</b>
            <small>Clinic updates and information</small>
          </article>
        </div>

        <div className="container urgent-note">
          <span className="eyebrow eyebrow--light">Important</span>
          <h2>For urgent medical concerns, do not wait for chat.</h2>
          <p>
            Clevia AI bukan emergency channel dan tidak menggantikan pemeriksaan langsung.
          </p>
        </div>
      </section>
    </>
  );
}
