import { Metadata } from "../../node_modules/next/types";
import "./globals.css";

export const metadata: Metadata = {
  title: "Competitor Report",
  description: "Competitor Report",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
