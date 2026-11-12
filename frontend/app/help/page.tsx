import { StaticPage } from "../../components/static-page";

/* Product help: factual orientation only. No support-desk, SLA, or
 * availability claims — those need owner confirmation. */
export default function HelpPage() {
  return (
    <StaticPage
      title="Help"
      intro="Orientation for working with CruiseShield AI."
      updated="2026-11-07"
      sections={[
        {
          heading: "Workspaces",
          paragraphs: [
            "The platform workspace holds transaction, signal, graph, and investigation views. Cases track assignments and evidence. The network explorer visualizes relationships, and replay runs scenarios.",
          ],
        },
        {
          heading: "Roles",
          paragraphs: [
            "Investigators work cases and evidence. Auditors review history. Administrators manage users and configuration. Your available actions always reflect your assigned role.",
          ],
        },
        {
          heading: "Evidence honesty",
          paragraphs: [
            "Verified facts, provider reports, estimates, and unavailable information are labeled separately throughout the product. An estimate is never presented as proof.",
          ],
        },
        {
          heading: "Getting support",
          paragraphs: [
            "Contact your organization administrator for access, role, or data questions. See the support page for the available channels.",
          ],
        },
      ]}
    />
  );
}
