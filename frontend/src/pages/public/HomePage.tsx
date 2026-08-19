import { Link } from "react-router-dom";
import { usePublicData } from "../../context/PublicDataContext";
import { ErrorState, LoadingState } from "../../components/Ui";
import { Icon } from "../../components/Icon";
import { formatCurrency } from "../../utils/format";
import {
  clinicInteriorImage,
  heroClinicImage,
  serviceImage,
  staffImage,
} from "../../data/visuals";

export default function HomePage() {
  const { clinic, services, staff, loading, error } = usePublicData();

  if (loading) return <LoadingState label="Menyiapkan Clevia..." />;
  if (error) return <ErrorState message={error} />;

  const featured = services.slice(0, 3);
  const featuredStaff = staff.slice(0, 3);

  return (
    <>
      <section className="classic-hero">
        <div className="classic-hero__orb classic-hero__orb--one" />
        <div className="classic-hero__orb classic-hero__orb--two" />

        <div className="container classic-hero__grid">
          <div className="classic-hero__copy">
            <span className="gold-pill">
              <Icon name="sparkle" size={14} /> Thoughtful aesthetic care
            </span>

            <h1>
              Beauty that feels
              <br />
              <em>like you.</em>
            </h1>

            <p>
              Clevia menghadirkan pengalaman beauty clinic yang tenang, personal,
              dan clinically considered—dengan informasi yang lebih jelas sebelum
              Anda mengambil keputusan.
            </p>

            <div className="classic-hero__actions">
              <Link className="btn btn--gold btn--large" to="/booking">
                Book consultation <Icon name="arrow" />
              </Link>
              <Link className="text-link" to="/treatments">
                Explore treatments <Icon name="arrow" />
              </Link>
            </div>

            <div className="classic-hero__proof">
              <span><Icon name="check" /> Doctor-led care</span>
              <span><Icon name="check" /> Personalized plan</span>
              <span><Icon name="check" /> Clear appointment status</span>
            </div>
          </div>

          <div className="classic-hero__visual">
            <div className="classic-hero__image">
              <img src={heroClinicImage} alt="Clevia clinic interior" />
              <span className="floating-note">
                <b>01</b>
                <em>Calm space.<br />Clear decisions.</em>
              </span>
            </div>

            <div className="hero-rating">
              <strong>4.9</strong>
              <div>
                <span className="hero-rating__stars">★★★★★</span>
                <small>client experience</small>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="trust-strip trust-strip--classic">
        <div className="container trust-strip__classic-inner">
          <p>Every treatment begins with a conversation, not a sales pitch.</p>
          <div>
            <span>SKIN HEALTH</span><i />
            <span>FACIAL</span><i />
            <span>LASER</span><i />
            <span>CONSULTATION</span>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="section-heading section-heading--classic">
            <div>
              <span className="eyebrow">Signature care</span>
              <h2>Designed around your skin,<br />not around trends.</h2>
            </div>

            <Link className="text-link" to="/treatments">
              View all treatments <Icon name="arrow" />
            </Link>
          </div>

          <div className="service-grid service-grid--classic">
            {featured.map((service, index) => (
              <article className="service-card service-card--classic" key={service.id}>
                <div className="service-card__image">
                  <img src={serviceImage(service, index)} alt={service.name} />
                  <span>0{index + 1}</span>
                </div>

                <div className="service-card__content">
                  <small>
                    {service.category} · {service.duration_minutes} min
                  </small>
                  <h3>{service.name}</h3>
                  <p>{service.description || service.short_description}</p>
                  <footer>
                    <b>From {formatCurrency(service.price_from, service.currency)}</b>
                    <Link
                      aria-label={`Book ${service.name}`}
                      to={`/booking?service=${service.id}`}
                    >
                      <Icon name="arrow" />
                    </Link>
                  </footer>
                </div>
              </article>
            ))}
          </div>

          <div className="info-ribbon">
            <article>
              <span>01</span>
              <div>
                <b>Know the service first</b>
                <p>Durasi, starting price, dan informasi utama tersedia sebelum booking.</p>
              </div>
            </article>
            <article>
              <span>02</span>
              <div>
                <b>Choose a real slot</b>
                <p>Availability berasal dari jadwal practitioner yang tersedia.</p>
              </div>
            </article>
            <article>
              <span>03</span>
              <div>
                <b>Stay in control</b>
                <p>Request tetap berstatus REQUESTED sampai tim klinik mengonfirmasi.</p>
              </div>
            </article>
          </div>
        </div>
      </section>

      <section className="manifesto-section">
        <div className="container manifesto-grid">
          <div className="manifesto-image">
            <img src={clinicInteriorImage} alt="Clevia treatment space" />
            <div className="manifesto-note">
              <Icon name="calendar" />
              <div>
                <b>Easy appointment</b>
                <small>Choose your preferred service and time.</small>
              </div>
            </div>
          </div>

          <div className="manifesto-copy">
            <span className="eyebrow">The Clevia approach</span>
            <h2>Refined results start with restraint.</h2>
            <p>
              Kami percaya aesthetic care yang baik tidak selalu berarti lebih
              banyak treatment. Yang lebih penting adalah memahami kebutuhan,
              memilih intervensi yang tepat, lalu mengukur progres secara realistis.
            </p>

            <ul>
              <li><Icon name="check" /> Consultation before recommendation</li>
              <li><Icon name="check" /> Transparent treatment planning</li>
              <li><Icon name="check" /> Human oversight when AI assists</li>
            </ul>

            <Link className="btn btn--light-gold" to="/about">
              Discover our philosophy <Icon name="arrow" />
            </Link>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="section-heading section-heading--classic">
            <div>
              <span className="eyebrow">Our practitioner</span>
              <h2>Medical judgment.<br />Human conversation.</h2>
            </div>
            <Link className="text-link" to="/doctors">
              Meet the team <Icon name="arrow" />
            </Link>
          </div>

          <div className="doctor-grid doctor-grid--classic">
            {featuredStaff.map((person, index) => (
              <article className="doctor-card doctor-card--classic" key={person.id}>
                <img src={staffImage(person, index)} alt={person.full_name} />
                <div>
                  <small>{person.specialty || person.staff_type}</small>
                  <h3>{person.full_name}</h3>
                  <p>{person.bio || "Measured care with patient-centered communication."}</p>
                </div>
              </article>
            ))}
          </div>

          {!featuredStaff.length && (
            <div className="state-card">
              <b>Practitioner profile will appear here.</b>
              <p>Public staff data has not been published yet.</p>
            </div>
          )}
        </div>
      </section>

      <section className="gold-intelligence">
        <div className="container gold-intelligence__grid">
          <div>
            <span className="eyebrow eyebrow--light">Clevia AI</span>
            <h2>Helpful when it should be. Human when it needs to be.</h2>
            <p>
              AI membantu menjawab informasi treatment, harga, kebijakan, profil
              klinik, dan alur appointment. Pertanyaan medis personal tetap
              membutuhkan practitioner atau staff.
            </p>
          </div>

          <div className="gold-intelligence__panel">
            <div>
              <span>Clinic information</span>
              <b>Grounded</b>
            </div>
            <div>
              <span>Service questions</span>
              <b>Evidence-based</b>
            </div>
            <div>
              <span>Appointment request</span>
              <b>Confirmation-gated</b>
            </div>
            <div>
              <span>Medical suitability</span>
              <b>Human handoff</b>
            </div>
          </div>
        </div>
      </section>

      <section className="gold-cta">
        <div className="container gold-cta__inner">
          <span className="eyebrow eyebrow--light">Start with clarity</span>
          <h2>Not sure which treatment<br />you actually need?</h2>
          <p>
            Mulai dari konsultasi. Clevia membantu menyusun langkah yang sesuai,
            bukan sekadar mengikuti treatment yang sedang ramai.
          </p>
          <Link className="btn btn--cream btn--large" to="/booking">
            Book a consultation <Icon name="arrow" />
          </Link>
        </div>
      </section>
    </>
  );
}
