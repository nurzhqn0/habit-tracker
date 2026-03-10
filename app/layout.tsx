import { Theme } from "@radix-ui/themes";
import "./globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Theme appearance="light">{children}</Theme>
      </body>
    </html>
  );
}
