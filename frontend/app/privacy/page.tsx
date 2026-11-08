import { StaticPage } from "../../components/static-page";

/* Privacy notice: describes implemented controls only. Retention and
 * jurisdiction specifics stay pending until decided and reviewed. */
export default function PrivacyPage() {
  return (
    <StaticPage
      title="Privacy"
      intro="How CruiseShield AI handles personal and sensitive information."
      updated="2026-11-07"
      sections={[
        {
          heading: "Data minimization",
          paragraphs: [
            "The product collects the minimum needed for its investigative purpose. Sensitive identifiers are masked by default and revealed only to authorized roles.",
          ],
        },
        {
          heading: "Isolation and access",
          paragraphs: [
            "Organization data is tenant-isolated. Access requires authentication, an authorized role, and, for sensitive operations, a documented purpose. Access to sensitive information is audited.",
          ],
        },
        {
          heading: "Retention",
          paragraphs: [
            "Retention, archival, and deletion schedules are pending owner authorization. No production purge runs until that decision is recorded.",
          ],
        },
        {
          heading: "Your requests",
          paragraphs: [
            "Questions or requests about personal information go to your organization administrator, who controls the organization's data and access decisions.",
          ],
        },
        {
          heading: "Review status",
          paragraphs: [
            "Jurisdiction-specific privacy reviews are pending. This notice will be updated as each review completes.",
          ],
        },
      ]}
    />
  );
}
