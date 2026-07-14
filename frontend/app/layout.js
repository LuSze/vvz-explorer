import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import ThemeProvider from "./ThemeProvider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "Course Catalog — VVZ ETH Zürich",
  description: "Semantic search for ETH Zurich lecture catalogue. Find lectures by meaning, not just keywords.",
};

import Footer from "./components/Footer";

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{
          __html: `(function(){try{var t=window.matchMedia("(prefers-color-scheme: dark)").matches?"eth-dark":"eth";document.documentElement.setAttribute("data-theme",t)}catch(e){}})();`,
        }} />
      </head>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased flex min-h-screen flex-col`}>
        <ThemeProvider>
          {children}
          <Footer />
        </ThemeProvider>
      </body>
    </html>
  );
}
