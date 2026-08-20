import { useMemo } from "react";
import { Link } from "react-router-dom";
import { usePublicData } from "../../context/PublicDataContext";
import { ErrorState, LoadingState } from "../../components/Ui";
import { Icon } from "../../components/Icon";
import { formatCurrency, humanize } from "../../utils/format";
import {
  clinicInteriorImage,
  heroClinicImage,
  serviceImage,
  staffImage,
} from "../../data/visuals";

export default function HomePage() {
  const { clinic, services, staff, loading, error } = usePublicData();

  const insights = useMemo(() => {
    if (!services.length) {
      return {
        categories: [] as string[],
        averageDuration: 0,
        minPrice: null as number | null,
        maxPrice: null as number | null,
      };
    }

    const categories = Array.from(new Set(services.map((service) => service.category)));
    const averageDuration = Math.round(
      services.reduce((sum, service) => sum + service.duration_minutes, 0) /
        services.length,
    );
    const prices = services
      .map((service) => Number(service.price_from))
      .filter((price) => Number.isFinite(price) && price > 0);

    return {
      categories,
      averageDuration,
      minPrice: prices.length ? Math.min(...prices) : null,
      maxPrice: prices.length ? Math.max(...prices) : null,
    };
  }, [services]);

  if (loading) return <LoadingState label="Menyiapkan Clevia..." />;
  if (error) return <ErrorState message={error} />;

  const featured = services.slice(0, 3);
  const comparison = services.slice(0, 5);
  const featuredStaff = staff.slice(0, 3);

  return (
    <>
      <section className="classic-hero classic-hero--pro">
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
              Temukan treatment, pahami estimasi harga dan durasinya, pilih jadwal
              yang tersedia, lalu lanjutkan dengan tim Clevia ketika keputusan
              membutuhkan konsultasi manusia.
            </p>

            <div className="classic-hero__actions">
              <Link className="btn btn--gold btn--large" to="/booking">
                Book consultation <Icon name="arrow" />
              </Link>
              <Link className="text-link" to="/treatments">
                Explore {services.length || "our"} treatments <Icon name="arrow" />
              </Link>
            </div>

            <div className="classic-hero__proof">
              <span><Icon name="check" /> Doctor-led care</span>
              <span><Icon name="check" /> Real service catalogue</span>
              <span><Icon name="check" /> Confirmation-gated booking</span>
            </div>
          </div>

          <div className="classic-hero__visual">
            <div className="classic-hero__image">
              <img src={heroClinicImage} alt="Clevia clinic interior" />
              <span className="floating-note">
                <b>{String(services.length || 3).padStart(2, "0")}</b>
                <em>Published services.<br />Clear starting points.</em>
              </span>
            </div>

            <div className="hero-rating hero-rating--data">
              <strong>{staff.length || 1}</strong>
              <div>
                <span className="hero-rating__label">PRACTITIONER</span>
                <small>public clinic profile</small>
              </div>
            </div>

            <div className="hero-data-card">
              <span>Starting from</span>
              <b>
                {insights.minPrice
                  ? formatCurrency(insights.minPrice, services[0]?.currency || "IDR")
                  : "Consult clinic"}
              </b>
              <small>Based on current published services</small>
            </div>
          </div>
        </div>
      </section>

      <section className="trust-strip trust-strip--classic">
        <div className="container trust-strip__classic-inner">
          <p>Every treatment begins with better information, not a sales pitch.</p>
          <div>
            {insights.categories.slice(0, 4).map((category, index) => (
              <span className="trust-category" key={category}>
                {humanize(category)}
                {index < Math.min(3, insights.categories.length - 1) && <i />}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="landing-data-strip">
        <div className="container landing-data-strip__grid">
          <article>
            <small>Published services</small>
            <strong>{services.length}</strong>
            <span>Live from clinic catalogue</span>
          </article>
          <article>
            <small>Treatment categories</small>
            <strong>{insights.categories.length}</strong>
            <span>{insights.categories.slice(0, 3).map(humanize).join(" · ") || "Clinic services"}</span>
          </article>
          <article>
            <small>Average duration</small>
            <strong>{insights.averageDuration || "—"}{insights.averageDuration ? "m" : ""}</strong>
            <span>Across published services</span>
          </article>
          <article>
            <small>Price range</small>
            <strong>
              {insights.minPrice
                ? formatCurrency(insights.minPrice, services[0]?.currency || "IDR")
                : "—"}
            </strong>
            <span>
              {insights.maxPrice
                ? `up to ${formatCurrency(insights.maxPrice, services[0]?.currency || "IDR")}`
                : "Ask Clevia"}
            </span>
          </article>
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
                  <em>{humanize(service.category)}</em>
                </div>

                <div className="service-card__content">
                  <small>{service.duration_minutes} min · starting price</small>
                  <h3>{service.name}</h3>
                  <p>{service.description || service.short_description}</p>
                  <footer>
                    <b>{formatCurrency(service.price_from, service.currency)}</b>
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

          <div className="info-ribbon info-ribbon--pro">
            <article>
              <span>01</span>
              <div>
                <b>Understand the service</b>
                <p>Bandingkan tujuan umum, durasi, dan starting price.</p>
              </div>
            </article>
            <article>
              <span>02</span>
              <div>
                <b>Check real availability</b>
                <p>Pilih tanggal dan slot dari availability practitioner.</p>
              </div>
            </article>
            <article>
              <span>03</span>
              <div>
                <b>Submit a REQUESTED appointment</b>
                <p>Jadwal belum final sebelum tim klinik mengonfirmasi.</p>
              </div>
            </article>
          </div>
        </div>
      </section>

      <section className="service-intelligence-section">
        <div className="container">
          <div className="section-heading section-heading--classic">
            <div>
              <span className="eyebrow">Compare before you choose</span>
              <h2>See the catalogue<br />in one clear view.</h2>
            </div>
            <p className="section-heading__copy">
              Data di bawah berasal dari layanan yang sedang dipublikasikan oleh
              Clevia, bukan angka marketing statis.
            </p>
          </div>

          <div className="service-comparison">
            <div className="service-comparison__head">
              <span>Treatment</span>
              <span>Category</span>
              <span>Duration</span>
              <span>Starting price</span>
              <span />
            </div>

            {comparison.map((service) => (
              <div className="service-comparison__row" key={service.id}>
                <div>
                  <span className="service-comparison__dot" />
                  <b>{service.name}</b>
                </div>
                <span>{humanize(service.category)}</span>
                <span>{service.duration_minutes} min</span>
                <strong>{formatCurrency(service.price_from, service.currency)}</strong>
                <Link to={`/booking?service=${service.id}`}>
                  <Icon name="arrow" />
                </Link>
              </div>
            ))}
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
                <b>One appointment flow</b>
                <small>Service → date → slot → clinic confirmation.</small>
              </div>
            </div>
          </div>

          <div className="manifesto-copy">
            <span className="eyebrow">The Clevia approach</span>
            <h2>Refined results start with restraint.</h2>
            <p>
              Tidak semua pertanyaan membutuhkan treatment baru. Clevia dirancang
              agar customer bisa memahami opsi terlebih dahulu, lalu berbicara
              dengan manusia ketika assessment atau judgement dibutuhkan.
            </p>

            <ul>
              <li><Icon name="check" /> Consultation before recommendation</li>
              <li><Icon name="check" /> Transparent treatment information</li>
              <li><Icon name="check" /> Human oversight when AI assists</li>
              <li><Icon name="check" /> Traceable appointment status</li>
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
        </div>
      </section>

      <section className="gold-intelligence gold-intelligence--pro">
        <div className="container gold-intelligence__grid">
          <div>
            <span className="eyebrow eyebrow--light">Clevia AI concierge</span>
            <h2>Structured answers, not a wall of text.</h2>
            <p>
              AI membantu menyusun informasi layanan, harga, durasi, profil klinik,
              dan appointment menjadi format yang lebih mudah dibaca. Untuk medical
              suitability, jalurnya tetap ke manusia.
            </p>

            <div className="ai-capability-row">
              <span><Icon name="check" /> Service lookup</span>
              <span><Icon name="check" /> Pricing context</span>
              <span><Icon name="check" /> Booking workflow</span>
              <span><Icon name="check" /> Human handoff</span>
            </div>
          </div>

          <div className="ai-preview-card">
            <div className="ai-preview-card__head">
              <span className="ai-preview-logo">C</span>
              <div><b>Clevia AI</b><small>Example structured answer</small></div>
            </div>
            <h3>Glow Facial Signature</h3>
            <p>Treatment yang berfokus pada cleansing, hydration, dan finishing glow.</p>
            <div className="ai-preview-facts">
              <div><span>Duration</span><b>60 minutes</b></div>
              <div><span>Starting price</span><b>{formatCurrency(featured[0]?.price_from, featured[0]?.currency || "IDR")}</b></div>
            </div>
            <ul>
              <li><span />Informasi umum tersedia melalui AI.</li>
              <li><span />Suitability personal tetap dikonsultasikan.</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="faq-section">
        <div className="container faq-grid">
          <div>
            <span className="eyebrow">Before you book</span>
            <h2>Common questions,<br />clearer answers.</h2>
            <p>
              Informasi operasional utama ditampilkan di depan supaya customer tidak
              harus selalu memulai dari chat.
            </p>
          </div>

          <div className="faq-list">
            <details open>
              <summary>Apakah appointment langsung confirmed?</summary>
              <p>
                Tidak. Request dari website maupun AI dibuat sebagai REQUESTED dan
                baru menjadi confirmed setelah diproses oleh tim Clevia.
              </p>
            </details>
            <details>
              <summary>Apakah AI bisa menentukan treatment yang cocok untuk saya?</summary>
              <p>
                AI dapat memberi informasi umum tentang layanan. Suitability personal,
                diagnosis, dan judgement medis tetap membutuhkan practitioner.
              </p>
            </details>
            <details>
              <summary>Apakah saya bisa melihat harga sebelum booking?</summary>
              <p>
                Ya. Published starting price dan durasi layanan ditampilkan pada
                catalogue dan halaman treatment.
              </p>
            </details>
            <details>
              <summary>Kalau butuh admin bagaimana?</summary>
              <p>
                Conversation dapat dialihkan dari AI ke staff ketika dibutuhkan.
              </p>
            </details>
          </div>
        </div>
      </section>

      <section className="gold-cta">
        <div className="container gold-cta__inner">
          <span className="eyebrow eyebrow--light">Start with clarity</span>
          <h2>Not sure where<br />to begin?</h2>
          <p>
            Explore treatment terlebih dahulu, tanyakan detail ke Clevia AI, atau
            langsung request consultation sesuai slot yang tersedia.
          </p>
          <div className="gold-cta__actions">
            <Link className="btn btn--cream btn--large" to="/booking">
              Book a consultation <Icon name="arrow" />
            </Link>
            <Link className="btn btn--glass btn--large" to="/treatments">
              View treatments
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
