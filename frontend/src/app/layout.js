import { Cormorant, Open_Sans } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";
import { MixpanelProvider } from "@/context/MixpanelProvider";
import { AuthProvider } from "@/context/AuthProvider";
import With404Boundary from '@/context/With404Boundary';


const open_sans = Open_Sans({
  subsets: ["latin"],
  variable: '--font-open-sans',
});
const cormorant = Cormorant({
  subsets: ["latin"],
  variable: '--font-cormorant',
});

export const metadata = {
  title: "Emmi",
  description: "An app designed for women who are training for marathons or looking to get exercise and stay fit, with a focus on injury prevention.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body  className={`${open_sans.className} ${open_sans.variable} ${cormorant.variable}`}>
        <MixpanelProvider>
          <AuthProvider>
            <With404Boundary>
              {children}
              <Toaster />
            </With404Boundary>
          </AuthProvider>
        </MixpanelProvider>
      </body>
    </html>
  );
}