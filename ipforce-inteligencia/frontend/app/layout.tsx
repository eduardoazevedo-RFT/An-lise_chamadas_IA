import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "IPForce Inteligencia",
  description: "Plataforma de analise de CDR e gravacoes",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="min-h-screen bg-background font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
