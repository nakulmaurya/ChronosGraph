import type { Metadata } from "next";
import "@xyflow/react/dist/style.css";
import "./globals.css";
export const metadata: Metadata = {
  title: "ChronosGraph · Visual oversight for coding agents",
  description:
    "See what your coding agents change—and the evidence behind it. A visual oversight and shared-context layer powered by FalkorDB.",
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
