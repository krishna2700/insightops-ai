import type { Metadata } from "next";

import { AppQueryProvider } from "@/lib/query-client";

import "./globals.css";

export const metadata: Metadata = {
  title: "InsightOps AI",
  description: "Ask a question in plain English, get live SQL, data, and charts.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppQueryProvider>{children}</AppQueryProvider>
      </body>
    </html>
  );
}
