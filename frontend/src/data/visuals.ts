import type { Service, Staff } from "../types";

const serviceImages: Record<string, string> = {
  "glow-facial-signature":
    "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?auto=format&fit=crop&w=1400&q=88",
  "acne-care":
    "https://images.unsplash.com/photo-1616394584738-fc6e612e71b9?auto=format&fit=crop&w=1400&q=88",
  "acne-care-consultation":
    "https://images.unsplash.com/photo-1616394584738-fc6e612e71b9?auto=format&fit=crop&w=1400&q=88",
  "laser-rejuvenation":
    "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=1400&q=88",
  "skin-booster":
    "https://images.unsplash.com/photo-1515377905703-c4788e51af15?auto=format&fit=crop&w=1400&q=88",
  "brightening-peel":
    "https://images.unsplash.com/photo-1598440947619-2c35fc9aa908?auto=format&fit=crop&w=1400&q=88",
  "contour-consultation":
    "https://images.unsplash.com/photo-1608248597279-f99d160bfcbc?auto=format&fit=crop&w=1400&q=88",
};

const serviceFallbacks = [
  "https://images.unsplash.com/photo-1570172619644-dfd03ed5d881?auto=format&fit=crop&w=1400&q=88",
  "https://images.unsplash.com/photo-1616394584738-fc6e612e71b9?auto=format&fit=crop&w=1400&q=88",
  "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?auto=format&fit=crop&w=1400&q=88",
];

const staffImages: Record<string, string> = {
  "dr-alina-pratama":
    "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=1000&q=88",
  "dr-nadia-arum":
    "https://images.unsplash.com/photo-1594824476967-48c8b964273f?auto=format&fit=crop&w=1000&q=88",
  "dr-keisha-mahendra":
    "https://images.unsplash.com/photo-1666887361002-a6e4b10eb4eb?auto=format&fit=crop&w=1000&q=88",
};

export const heroClinicImage =
  "https://images.unsplash.com/photo-1629909613654-28e377c37b09?auto=format&fit=crop&w=1600&q=90";

export const clinicInteriorImage =
  "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=1500&q=90";

export function serviceImage(service: Service, index = 0): string {
  return (
    serviceImages[service.slug] ||
    serviceFallbacks[index % serviceFallbacks.length]
  );
}

export function staffImage(staff: Staff, index = 0): string {
  return (
    staffImages[staff.slug] ||
    [
      "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=1000&q=88",
      "https://images.unsplash.com/photo-1594824476967-48c8b964273f?auto=format&fit=crop&w=1000&q=88",
    ][index % 2]
  );
}
