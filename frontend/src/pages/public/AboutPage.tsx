import { usePublicData } from "../../context/PublicDataContext";
import { clinicInteriorImage } from "../../data/visuals";
import { ErrorState, LoadingState } from "../../components/Ui";
import { Icon } from "../../components/Icon";

export default function AboutPage() {
  const { clinic, loading, error } = usePublicData();

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <>
      <section className="page-hero page-hero--gold page-hero--about">
        <div className="container">
          <span className="gold-pill">About Clevia</span>
          <h1>{clinic?.tagline || "Confidence, refined."}</h1>
          <p>
            {clinic?.description ||
              "Beauty clinic modern dengan pendekatan personal, terukur, dan tenang."}
          </p>
        </div>
      </section>

      <section className="section">
        <div className="container about-story-grid">
          <div className="about-story-image">
            <img src={clinicInteriorImage} alt="Clevia clinic interior" />
          </div>

          <div className="about-story-copy">
            <span className="eyebrow">Our philosophy</span>
            <h2>Less noise. More clarity. Better decisions.</h2>
            <p className="lead">
              Clevia dibangun untuk membuat pengalaman beauty clinic terasa lebih
              terarah—dari discovery, consultation, appointment, sampai follow-up.
            </p>
            <p>
              AI membantu bagian yang repetitif dan cepat. Staff dan practitioner
              tetap memegang bagian yang membutuhkan judgement, assessment, dan
              tanggung jawab manusia.
            </p>

            <div className="about-checks">
              <span><Icon name="check" /> Transparent information</span>
              <span><Icon name="check" /> Human-controlled appointment flow</span>
              <span><Icon name="check" /> AI with defined boundaries</span>
            </div>
          </div>
        </div>

        <div className="container value-grid value-grid--gold">
          <article><span>01</span><h3>Personal</h3><p>Konteks pelanggan tidak diperlakukan sebagai tiket generik.</p></article>
          <article><span>02</span><h3>Grounded</h3><p>Informasi digital dibatasi pada data dan knowledge yang tersedia.</p></article>
          <article><span>03</span><h3>Measured</h3><p>Treatment dan appointment memiliki status yang dapat dilacak.</p></article>
          <article><span>04</span><h3>Human-led</h3><p>Medical suitability tetap berada di luar otoritas agent.</p></article>
        </div>
      </section>
    </>
  );
}
