import { StaticPage } from "../../components/static-page";

/* Legal notice: draft status stated plainly. Nothing here is legal
 * advice, and no license or compliance is claimed. */
export default function LegalPage() {
  return (
    <StaticPage
      title="Legal"
      intro="Legal notices for CruiseShield AI. This page is a draft pending owner and counsel review."
      updated="2026-11-07"
      sections={[
        {
          heading: "License",
          paragraphs: [
            "The public repository license has not been selected. Until the owner records a license choice, no reuse rights are granted beyond viewing.",
          ],
        },
        {
          heading: "Regulatory status",
          paragraphs: [
            "Financial-crime, data-protection, and telecom obligations differ by jurisdiction. Required legal reviews are pending, and this product makes no claim of regulatory approval or compliance.",
          ],
        },
        {
          heading: "Investigative use",
          paragraphs: [
            "Risk scores, signals, and relationship views are investigative inputs, not determinations of wrongdoing. Consequential decisions require qualified human review.",
          ],
        },
        {
          heading: "Not legal advice",
          paragraphs: [
            "Nothing on this page or in this product constitutes legal advice. Consult qualified counsel for your jurisdiction and use case.",
          ],
        },
      ]}
    />
  );
}
