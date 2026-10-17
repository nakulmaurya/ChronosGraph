import type { Metadata } from "next";
import "@xyflow/react/dist/style.css";
import "./globals.css";
export const metadata: Metadata = {
  title: "ChronosGraph · Repository Command Center",
  description:
    "Explore repository dependencies, inspect functions, preview changes, and follow coding-agent activity with FalkorDB.",
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
