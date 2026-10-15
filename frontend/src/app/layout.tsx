import type { Metadata } from "next";
import "@xyflow/react/dist/style.css";
import "./globals.css";
export const metadata: Metadata = {
  title: "ChronosGraph · Flight Recorder",
  description:
    "Local FalkorDB graph workbench. Disposable audits, policy lineage and verified playbook replay.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
