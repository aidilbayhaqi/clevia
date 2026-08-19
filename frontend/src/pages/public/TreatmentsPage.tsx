import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { usePublicData } from "../../context/PublicDataContext";
import { ErrorState, LoadingState } from "../../components/Ui";
import { formatCurrency, humanize } from "../../utils/format";
import { serviceImage } from "../../data/visuals";
import { Icon } from "../../components/Icon";

export default function TreatmentsPage() {
  const { services, loading, error } = usePublicData();
  const [category, setCategory] = useState("all");
  const [query, setQuery] = useState("");

  const categories = useMemo(
    () => ["all", ...Array.from(new Set(services.map((service) => service.category)))],
    [services],
  );

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return services.filter((service) => {
      const categoryMatch = category === "all" || service.category === category;
      const textMatch =
        !needle ||
        service.name.toLowerCase().includes(needle) ||
        (service.description || "").toLowerCase().includes(needle);
      return categoryMatch && textMatch;
    });
  }, [category, query, services]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  return (
    <>
      <section className="page-hero page-hero--gold">
        <div className="container">
          <span className="gold-pill">Treatment catalogue</span>
          <h1>Understand the treatment<br /><em>before choosing it.</em></h1>
          <p>
            Bandingkan treatment, durasi, starting price, dan konteks layanan
            sebelum masuk ke proses appointment.
          </p>
        </div>
      </section>

      <section className="section section--catalogue">
        <div className="container">
          <div className="catalog-toolbar">
            <div className="filter-pills filter-pills--gold">
              {categories.map((item) => (
                <button
                  key={item}
                  className={category === item ? "is-active" : ""}
                  onClick={() => setCategory(item)}
                >
                  {humanize(item)}
                </button>
              ))}
            </div>

            <label className="search-field search-field--gold">
              <Icon name="search" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search treatment..."
              />
            </label>
          </div>

          <div className="catalogue-grid">
            {filtered.map((service, index) => (
              <article className="catalogue-card" key={service.id}>
                <div className="catalogue-card__image">
                  <img src={serviceImage(service, index)} alt={service.name} />
                  <span>{humanize(service.category)}</span>
                </div>

                <div className="catalogue-card__body">
                  <div className="catalogue-card__meta">
                    <span>{service.duration_minutes} min</span>
                    <span>{formatCurrency(service.price_from, service.currency)}</span>
                  </div>
                  <h2>{service.name}</h2>
                  <p>{service.description || service.short_description}</p>
                  <Link className="btn btn--light-gold" to={`/booking?service=${service.id}`}>
                    Check availability <Icon name="arrow" />
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
