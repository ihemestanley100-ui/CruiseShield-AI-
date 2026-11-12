import { StaticPage } from "../../components/static-page";

/* Support channels: only mechanisms that exist are named. No public
 * helpdesk, email, phone, SLA, or response-time claims. */
export default function SupportPage() {
  return (
    <StaticPage
      title="Support"
      intro="How to get help with CruiseShield AI."
      updated="2026-11-07"
      sections={[
        {
          heading: "Organization administrator first",
          paragraphs: [
            "Access, roles, organization membership, and data questions go to your organization administrator, who can manage users and configuration inside the product.",
          ],
        },
        {
          heading: "In-product notices",
          paragraphs: [
            "Security notices about your own sign-ins and account changes appear in the product notification area when your organization enables them.",
          ],
        },
        {
          heading: "What is not offered here",
          paragraphs: [
            "This page does not list a public support desk, email address, phone number, or response-time commitment. Any such channel will be named here only after the owner confirms it.",
          ],
        },
      ]}
    />
  );
}
