import { Theme } from "@radix-ui/themes";
import "./globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <Theme appearance="light">{children}</Theme>
      </body>
    </html>
  );
}
