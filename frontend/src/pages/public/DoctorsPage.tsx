import { Link } from "react-router-dom";
import { usePublicData } from "../../context/PublicDataContext";
import { ErrorState, LoadingState } from "../../components/Ui";
import { humanize } from "../../utils/format";
import { staffImage } from "../../data/visuals";
import { Icon } from "../../components/Icon";

export default function DoctorsPage() {
  const { staff, loading, error } = usePublicData();

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <>
      <section className="page-hero page-hero--gold">
        <div className="container">
          <span className="gold-pill">Our practitioner</span>
          <h1>Medical judgment.<br /><em>Human conversation.</em></h1>
          <p>
            Informasi digital mempercepat keputusan. Assessment dan treatment
            suitability tetap berada pada practitioner.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <div className="doctor-grid doctor-grid--classic">
            {staff.map((person, index) => (
              <article className="doctor-card doctor-card--classic doctor-card--detail" key={person.id}>
                <img src={staffImage(person, index)} alt={person.full_name} />
                <div>
                  <small>{humanize(person.staff_type)}</small>
                  <h3>{person.full_name}</h3>
                  <b>{person.title || person.specialty || "Clinic Practitioner"}</b>
                  <p>{person.bio || "Personal consultation and measured treatment planning."}</p>
                  <span className="doctor-specialty">
                    {person.specialty || "Aesthetic care"}
                  </span>
                </div>
              </article>
            ))}
          </div>

          <div className="editorial-principles">
            <article><span>01</span><h3>Assessment before recommendation</h3><p>Informasi umum tidak menggantikan evaluasi personal.</p></article>
            <article><span>02</span><h3>Measured treatment planning</h3><p>Plan dibuat bertahap, bukan berdasarkan tren semata.</p></article>
            <article><span>03</span><h3>Human handoff when needed</h3><p>Pertanyaan personal dan sensitif diarahkan ke tim klinik.</p></article>
          </div>

          <div className="center-cta">
            <Link className="btn btn--gold btn--large" to="/booking">
              Book consultation <Icon name="arrow" />
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
