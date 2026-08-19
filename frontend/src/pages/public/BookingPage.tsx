import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { publicApi } from "../../api/publicApi";
import { usePublicData } from "../../context/PublicDataContext";
import type { AvailabilitySlot, Service } from "../../types";
import { formatCurrency, formatDateTime, todayIso } from "../../utils/format";
import { ErrorState, LoadingState } from "../../components/Ui";
import { Icon } from "../../components/Icon";

type Step = "service" | "date" | "slot" | "details" | "done";

export default function BookingPage() {
  const { services, loading, error } = usePublicData();
  const [params] = useSearchParams();
  const [step, setStep] = useState<Step>("service");
  const [serviceId, setServiceId] = useState(params.get("service") || "");
  const [date, setDate] = useState("");
  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [slot, setSlot] = useState<AvailabilitySlot | null>(null);
  const [checking, setChecking] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");
  const [appointmentId, setAppointmentId] = useState("");
  const [details, setDetails] = useState({ full_name: "", phone: "", email: "", note: "" });

  const selectedService = useMemo(() => services.find((item) => item.id === serviceId) || null, [serviceId, services]);

  useEffect(() => {
    if (serviceId && services.some((item) => item.id === serviceId)) setStep("date");
  }, [serviceId, services]);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  function chooseService(service: Service) {
    setServiceId(service.id);
    setStep("date");
    setSlots([]);
    setSlot(null);
  }

  async function checkAvailability() {
    if (!serviceId || !date) return;
    setChecking(true);
    setFormError("");
    try {
      setSlots(await publicApi.availability(serviceId, date));
      setStep("slot");
    } catch (reason) {
      setFormError(reason instanceof Error ? reason.message : "Gagal memeriksa slot.");
    } finally {
      setChecking(false);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!slot || !selectedService) return;
    setSubmitting(true);
    setFormError("");
    try {
      const appointment = await publicApi.requestAppointment({
        full_name: details.full_name.trim(),
        phone: details.phone.trim(),
        email: details.email.trim() || null,
        service_id: selectedService.id,
        staff_id: slot.staff_id,
        starts_at: slot.starts_at,
        note: details.note.trim() || null,
      });
      setAppointmentId(appointment.id);
      setStep("done");
    } catch (reason) {
      setFormError(reason instanceof Error ? reason.message : "Appointment request gagal.");
    } finally {
      setSubmitting(false);
    }
  }

  const steps = [["service", "Treatment"], ["date", "Date"], ["slot", "Time"], ["details", "Details"]] as const;

  return (
    <section className="booking-shell">
      <div className="container">
        <div className="booking-heading"><span className="gold-pill">Appointment request</span><h1>Book with clarity.<br /><em>Confirm with confidence.</em></h1><p>Jadwal yang dikirim berstatus REQUESTED sampai tim Clevia mengonfirmasi.</p></div>

        {step !== "done" && (
          <div className="booking-progress">
            {steps.map(([id, label], index) => {
              const currentIndex = steps.findIndex(([value]) => value === step);
              return <div key={id} className={index <= currentIndex ? "is-active" : ""}><span>{index + 1}</span><b>{label}</b></div>;
            })}
          </div>
        )}

        <div className="booking-card">
          {step === "service" && (
            <div>
              <div className="booking-card__head"><span>STEP 1</span><h2>Select a treatment</h2><p>Pilih layanan yang ingin kamu request.</p></div>
              <div className="booking-service-options">{services.map((service) => <button key={service.id} onClick={() => chooseService(service)}><div><span>{service.category}</span><b>{service.name}</b><small>{service.duration_minutes} minutes</small></div><strong>{formatCurrency(service.price_from, service.currency)}</strong></button>)}</div>
            </div>
          )}

          {step === "date" && selectedService && (
            <div className="booking-two-column">
              <div>
                <button className="back-link" onClick={() => setStep("service")}>← Change treatment</button>
                <div className="booking-card__head"><span>STEP 2</span><h2>Choose a date</h2><p>Availability akan dibaca langsung dari jadwal practitioner.</p></div>
                <label className="field"><span>Date</span><input type="date" min={todayIso()} value={date} onChange={(event) => setDate(event.target.value)} /></label>
                {formError && <div className="form-error">{formError}</div>}
                <button className="btn btn--dark btn--wide" disabled={!date || checking} onClick={() => void checkAvailability()}>{checking ? "Checking..." : "Check availability"} <Icon name="arrow" /></button>
              </div>
              <BookingSummary service={selectedService} slot={null} />
            </div>
          )}

          {step === "slot" && selectedService && (
            <div className="booking-two-column">
              <div>
                <button className="back-link" onClick={() => setStep("date")}>← Change date</button>
                <div className="booking-card__head"><span>STEP 3</span><h2>Available times</h2><p>{date ? `Real slots for ${date}` : "Select a slot."}</p></div>
                <div className="slot-grid">{slots.map((item) => <button key={`${item.staff_id}-${item.starts_at}`} className={slot?.starts_at === item.starts_at ? "is-active" : ""} onClick={() => setSlot(item)}><b>{new Intl.DateTimeFormat("id-ID", { hour: "2-digit", minute: "2-digit", timeZone: "Asia/Jakarta" }).format(new Date(item.starts_at))}</b><span>{item.staff_name}</span></button>)}</div>
                {!slots.length && <div className="state-card"><b>No slots available.</b><p>Pilih tanggal lain untuk melihat availability.</p></div>}
                <button className="btn btn--dark btn--wide" disabled={!slot} onClick={() => setStep("details")}>Continue <Icon name="arrow" /></button>
              </div>
              <BookingSummary service={selectedService} slot={slot} />
            </div>
          )}

          {step === "details" && selectedService && slot && (
            <div className="booking-two-column">
              <form onSubmit={submit}>
                <button type="button" className="back-link" onClick={() => setStep("slot")}>← Change time</button>
                <div className="booking-card__head"><span>STEP 4</span><h2>Your contact details</h2><p>Tim Clevia menggunakan data ini untuk follow-up appointment.</p></div>
                <div className="form-grid">
                  <label className="field field--full"><span>Full name</span><input required value={details.full_name} onChange={(e) => setDetails({ ...details, full_name: e.target.value })} /></label>
                  <label className="field"><span>WhatsApp / phone</span><input required value={details.phone} onChange={(e) => setDetails({ ...details, phone: e.target.value })} /></label>
                  <label className="field"><span>Email <small>optional</small></span><input type="email" value={details.email} onChange={(e) => setDetails({ ...details, email: e.target.value })} /></label>
                  <label className="field field--full"><span>Note <small>optional</small></span><textarea rows={3} value={details.note} onChange={(e) => setDetails({ ...details, note: e.target.value })} /></label>
                </div>
                {formError && <div className="form-error">{formError}</div>}
                <button className="btn btn--dark btn--wide" disabled={submitting}>{submitting ? "Submitting..." : "Submit appointment request"} <Icon name="arrow" /></button>
                <small className="form-notice">Submitting this form creates a REQUESTED appointment, not a final clinic confirmation.</small>
              </form>
              <BookingSummary service={selectedService} slot={slot} />
            </div>
          )}

          {step === "done" && (
            <div className="booking-success"><span className="success-mark"><Icon name="check" size={28} /></span><span className="eyebrow">Request received</span><h2>Your appointment is now REQUESTED.</h2><p>Tim Clevia akan melakukan konfirmasi. Simpan reference ID berikut jika diperlukan.</p><code>{appointmentId}</code><a className="btn btn--dark" href="/">Back to home</a></div>
          )}
        </div>
      </div>
    </section>
  );
}

function BookingSummary({ service, slot }: { service: Service; slot: AvailabilitySlot | null }) {
  return (
    <aside className="booking-summary">
      <span>YOUR SELECTION</span><h3>{service.name}</h3>
      <div><small>Duration</small><b>{service.duration_minutes} minutes</b></div>
      <div><small>Starting price</small><b>{formatCurrency(service.price_from, service.currency)}</b></div>
      {slot && <><div><small>Practitioner</small><b>{slot.staff_name}</b></div><div><small>Schedule</small><b>{formatDateTime(slot.starts_at)}</b></div></>}
      <p>Final treatment suitability and clinic confirmation remain with the Clevia team.</p>
    </aside>
  );
}
